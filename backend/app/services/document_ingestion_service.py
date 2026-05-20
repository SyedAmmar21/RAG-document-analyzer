import os
import logging
from app.services.text_extraction_service import extract_text
from app.services.document_service import (
    create_document_record,
)
from app.services.metadata_extraction_service import (
    extract_metadata
)
from app.services.vector_service import (
    index_document,
    es,
)
from app.db.database import get_connection
from app.services.hybrid_embedding_service import (
    generate_hybrid_embedding,
)
from app.services.domain_similarity_service import (
    get_best_matching_domain
)
from app.services.metadata_service import save_metadata
from app.services.domain_assignment_service import assign_domain

from app.services.domain_service import (
    assign_document_to_domain,
    get_all_domains,
    get_domain_by_name,
)


logger = logging.getLogger(__name__)


def _extract_source_url_from_text(extracted_text: str) -> str | None:
    """Extract source URL from document text header."""
    lines = extracted_text.split("\n")
    for line in lines[:10]:  # Check first 10 lines
        if line.startswith("Source URL:"):
            url = line.replace("Source URL:", "", 1).strip()
            return url if url else None
    return None


def _cleanup_failed_document(document_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM document_metadata WHERE document_id = ?",
        (document_id,)
    )
    cursor.execute(
        "DELETE FROM document_domains WHERE document_id = ?",
        (document_id,)
    )
    cursor.execute(
        "DELETE FROM documents WHERE id = ?",
        (document_id,)
    )
    conn.commit()
    conn.close()

    try:
        es.delete_by_query(
            index="documents",
            body={
                "query": {
                    "term": {
                        "document_id": document_id
                    }
                }
            },
            conflicts="proceed",
            refresh=True,
        )
    except Exception:
        logger.exception("Failed to clean Elasticsearch chunks for document %s", document_id)


def process_document_pipeline(
    file_path: str,
    original_filename: str
):
    document_id = None

    # Extract text
    extracted_text = extract_text(file_path)

    if not extracted_text or not extracted_text.strip():
        raise ValueError("No extractable text found in document.")

    # File metadata
    file_size = os.path.getsize(file_path)

    file_type = (
        os.path.splitext(original_filename)[1]
        .replace(".", "")
    )

    # Create DB document
    document_id = create_document_record(
        file_path=file_path,
        file_size=file_size,
        file_type=file_type
    )

    try:
        # Metadata extraction
        metadata_suggestions = extract_metadata(
            extracted_text
        )

        saved_metadata = save_metadata(
            document_id,
            metadata_suggestions
        )

        # Extract and save source URL if present
        source_url = _extract_source_url_from_text(extracted_text)
        if source_url:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO document_metadata (document_id, field, value)
                VALUES (?, ?, ?)
                """,
                (document_id, "source_url", source_url)
            )
            conn.commit()
            conn.close()

        # Vector indexing
        index_document(
            document_id,
            extracted_text
        )

        # Hybrid semantic embedding
        document_embedding = generate_hybrid_embedding(
            document_id=document_id,
            metadata=metadata_suggestions,
        )

        # Domain assignment
        domain_suggestion = get_best_matching_domain(
            document_embedding
        )

        assigned_domain = None

        if not domain_suggestion:
            available_domains = [
                domain
                for domain in get_all_domains()
                if domain.get("id") != "unorganized"
            ]
            fallback = assign_domain(metadata_suggestions, available_domains)
            fallback_name = fallback.get("suggested_domain")
            fallback_domain = get_domain_by_name(fallback_name) if fallback_name else None

            if fallback_domain:
                domain_suggestion = {
                    "id": fallback_domain["id"],
                    "name": fallback_domain["name"],
                    "similarity": fallback.get("confidence"),
                    "assignment_method": "metadata_fallback",
                }

        if domain_suggestion:
            assigned_domain = assign_document_to_domain(
                document_id,
                domain_suggestion["id"],
                domain_suggestion.get("similarity")
            )
    except Exception:
        if document_id:
            _cleanup_failed_document(document_id)
        logger.exception("Document ingestion failed for %s", original_filename)
        raise

    return {
        "document_id": document_id,
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "metadata_suggestions": metadata_suggestions,
        "saved_metadata": saved_metadata,
        "domain_suggestion": domain_suggestion,
        "assigned_domain": assigned_domain,
        "preview": extracted_text[:300]
    }
