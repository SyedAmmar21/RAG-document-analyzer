from fastapi import APIRouter, UploadFile, File
import os

from app.services.file_service import (
    validate_file_type,
    validate_file_size,
    save_file
)
from app.services.text_extraction_service import extract_text
from app.services.document_service import (
    create_document_record,
    find_document_by_upload_name,
)

from app.services.hybrid_embedding_service import (
    generate_hybrid_embedding,
)

from app.services.domain_similarity_service import get_best_matching_domain

from app.services.domain_service import get_all_domains, get_document_domain
from app.services.metadata_extraction_service import extract_metadata
from app.services.metadata_service import get_metadata_values
from app.services.vector_service import index_document 

router = APIRouter()


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    # Validate
    validate_file_type(file)
    validate_file_size(file)

    existing_document = find_document_by_upload_name(file.filename)

    if existing_document:
        return {
            "message": f"This file is already in the repository at document number {existing_document['number']}. Reusing the existing document.",
            "document_id": existing_document["document_id"],
            "file_name": existing_document["file_name"],
            "file_path": existing_document["file_path"],
            "document_number": existing_document["number"],
            "duplicate": True,
            "metadata_suggestions": get_metadata_values(existing_document["document_id"]),
            "domain_suggestion": get_document_domain(existing_document["document_id"])
        }

    file_path = save_file(file)

    extracted_text = extract_text(file_path)

    # Get metadata
    file_size = os.path.getsize(file_path)
    file_type = os.path.splitext(file.filename)[1].replace(".", "")

    # Store in DB
    document_id = create_document_record(
        file_path=file_path,
        file_size=file_size,
        file_type=file_type
    )

    # Extract metadata
    metadata_suggestions = extract_metadata(extracted_text)

    # IMPORTANT:
    # Index document FIRST so chunk embeddings
    # exist inside Elasticsearch
    index_document(
        document_id,
        extracted_text
    )

    # Generate hybrid semantic embedding
    # (metadata + chunk centroid)
    document_embedding = generate_hybrid_embedding(
        document_id=document_id,
        metadata=metadata_suggestions,
    )

    # Find best semantic domain
    domain_suggestion = get_best_matching_domain(
        document_embedding
    )

    return {
        "message": "File uploaded and indexed",
        "document_id": document_id,
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "preview": extracted_text[:300],
        "metadata_suggestions": metadata_suggestions,
        "domain_suggestion": domain_suggestion
    }