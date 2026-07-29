import asyncio
import mimetypes
from sqlite3 import IntegrityError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import ELASTICSEARCH_HOST
from app.core.paths import resolve_storage_path, UPLOAD_DIR, NEWS_ARTICLES_DIR, OUTPUT_DIR
from app.db.database import get_connection
from app.services.document_service import get_document_by_id
from app.services.domain_service import (
    assign_document_to_domain,
    create_domain,
    delete_domain,
    get_all_domains,
    get_document_domain,
    get_domain_by_id,
    get_unorganized_documents,
    update_domain,
)
from app.services.metadata_service import get_metadata as get_saved_metadata, save_metadata
from app.services.domain_service import get_documents_by_domain
from app.services.office_document_service import OfficeDocumentService
from app.services.sandbox.session_store import (
    WorkingDocument,
    clear_current_document,
    clear_current_document_for_filename,
    get_backend,
    get_current_document,
    set_current_document,
)
from app.services.domain_centroid_service import (
    recompute_domain_centroid
)
router = APIRouter()

es = Elasticsearch(
    ELASTICSEARCH_HOST,
    request_timeout=30,
    verify_certs=False
)


class MetadataSaveRequest(BaseModel):
    document_id: str
    metadata: Dict[str, Any]
    domain_id: Optional[int] = None
    confidence: Optional[float] = None


class DocumentMetadataUpdateRequest(BaseModel):
    metadata: Dict[str, Any]
    domain_id: Optional[int] = None
    confidence: Optional[float] = None


class DomainCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class DomainUpdateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class PresentationGenerationRequest(BaseModel):
    title: str
    slides: list[str]


class ActiveOutputRequest(BaseModel):
    thread_id: str
    file_name: str


EDITABLE_OUTPUT_TYPES = {".docx", ".pptx", ".xlsx"}


def _resolve_output_file(filename: str) -> Path:
    """Return a generated output file only when it is directly inside OUTPUT_DIR."""
    if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid output filename")

    output_dir = OUTPUT_DIR.resolve()
    output_path = (OUTPUT_DIR / filename).resolve()

    try:
        output_path.relative_to(output_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid output filename")

    return output_path


def _output_file_response(output_path: Path, *, disposition: str) -> FileResponse:
    media_type, _ = mimetypes.guess_type(str(output_path))
    safe_file_name = output_path.name.replace('"', "")

    return FileResponse(
        str(output_path),
        media_type=media_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'{disposition}; filename="{safe_file_name}"',
        },
    )


def _is_editable_output(output_path: Path) -> bool:
    return output_path.suffix.lower() in EDITABLE_OUTPUT_TYPES


def _upload_output_to_sandbox(sandbox_backend, output_path: Path) -> None:
    upload_file_bytes = getattr(sandbox_backend, "upload_file_bytes", None)
    if not callable(upload_file_bytes):
        raise RuntimeError("Sandbox backend does not support file uploads")

    upload_file_bytes(
        f"/workspace/output/{output_path.name}",
        output_path.read_bytes(),
    )


@router.get("/documents")
async def get_documents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        ROW_NUMBER() OVER (ORDER BY created_date DESC) AS number,
        id,
        file_path,
        created_date
    FROM documents
    """)
    rows = cursor.fetchall()

    document_ids = [row["id"] for row in rows]
    published_dates = {}
    source_urls = {}
    document_domains = {}

    if document_ids:
        placeholders = ",".join("?" for _ in document_ids)
        
        # Fetch published dates and source URLs from metadata
        cursor.execute(
            f"""
            SELECT document_id, field, value
            FROM document_metadata
            WHERE field IN ('published_date', 'source_url')
              AND document_id IN ({placeholders})
            """,
            document_ids,
        )

        for row in cursor.fetchall():
            if row["field"] == "published_date" and row["value"]:
                published_dates[row["document_id"]] = row["value"]
            elif row["field"] == "source_url" and row["value"]:
                source_urls[row["document_id"]] = row["value"]

        # Fetch domains for each document
        cursor.execute(
            f"""
            SELECT dd.document_id, d.name
            FROM document_domains dd
            JOIN domains d ON dd.domain_id = d.id
            WHERE dd.document_id IN ({placeholders})
            """,
            document_ids,
        )

        for row in cursor.fetchall():
            if row["document_id"] not in document_domains:
                document_domains[row["document_id"]] = []
            document_domains[row["document_id"]].append(row["name"])

    conn.close()

    documents = [
        {
            "number": row["number"],
            "document_id": row["id"],
            "file_name": Path(row["file_path"]).name,
            "published_date": published_dates.get(row["id"]),
            "status": "ready",
            "created_date": row["created_date"],
            "domains": document_domains.get(row["id"], []),
            "source_url": source_urls.get(row["id"]),
        }
        for row in rows
    ]

    return {"documents": documents}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT file_path FROM documents WHERE id = ?",
        (document_id,)
    )
    row = cursor.fetchone()

    cursor.execute(
        "SELECT file_path FROM documents WHERE id = ?",
        (document_id,)
    )
    row = cursor.fetchone()

    cursor.execute(
        """
        SELECT domain_id
        FROM document_domains
        WHERE document_id = ?
        """,
        (document_id,)
    )

    domain_row = cursor.fetchone()

    domain_id = (
        domain_row["domain_id"]
        if domain_row
        else None
    )

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    relative_path = row["file_path"]

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

    # Delete the actual file
    if relative_path:
        try:
            absolute_path = resolve_storage_path(relative_path)
            if absolute_path.exists():
                absolute_path.unlink()
        except (ValueError, OSError) as e:
            # If path resolution fails or file doesn't exist, that's okay
            # Document record was already deleted from DB
            pass

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

    if domain_id:
        recompute_domain_centroid(domain_id)

    return {"message": "Document deleted successfully"}


@router.get("/documents/{document_id}/view")
async def view_document(document_id: str):
    document = get_document_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    stored_path = document["file_path"]
    file_name = document["file_name"]

    try:
        # Try to resolve the stored path
        absolute_path = resolve_storage_path(stored_path)
        
        # If path doesn't exist and is absolute (old database record), try to find it locally
        print("STORED PATH:", stored_path)
        print("RESOLVED PATH:", absolute_path)
        print("EXISTS:", absolute_path.exists())
        if not absolute_path.exists() and absolute_path.is_absolute():
            # Check uploads
            local_upload_path = UPLOAD_DIR / file_name
            if local_upload_path.exists():
                absolute_path = local_upload_path
            else:
                # Check news articles
                local_news_path = NEWS_ARTICLES_DIR / file_name
                if local_news_path.exists():
                    absolute_path = local_news_path
                else:
                    raise HTTPException(status_code=404, detail="Document file not found")
        
        if not absolute_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        media_type, _ = mimetypes.guess_type(str(absolute_path))
        safe_file_name = file_name.replace('"', "")

        return FileResponse(
            str(absolute_path),
            media_type=media_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'inline; filename="{safe_file_name}"',
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Invalid document path: {str(e)}")


@router.get("/outputs")
async def list_output_files():
    """List files persisted by the AI agent for the Output workspace tab."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_files = []

    for output_path in OUTPUT_DIR.iterdir():
        if not output_path.is_file():
            continue

        try:
            resolved_path = _resolve_output_file(output_path.name)
            stat = resolved_path.stat()
        except (HTTPException, OSError):
            # Do not expose broken or unsafe filesystem entries.
            continue

        output_files.append(
            {
                "file_name": output_path.name,
                "size": stat.st_size,
                "created_date": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
                "file_type": output_path.suffix.lower().lstrip("."),
                "is_editable": _is_editable_output(output_path),
            }
        )

    output_files.sort(key=lambda item: item["created_date"], reverse=True)
    return {"outputs": output_files}


@router.get("/outputs/active")
async def get_active_output(thread_id: str):
    """Return the one active working document for the supplied chat thread."""
    current_document = get_current_document(thread_id)

    if current_document is None:
        return {"active_output": None}

    return {
        "active_output": {
            "file_name": current_document.filename,
            "file_type": current_document.file_type,
        }
    }


@router.put("/outputs/active")
async def set_active_output(request: ActiveOutputRequest):
    """Make a saved Office output the active file in this chat's sandbox."""
    output_path = _resolve_output_file(request.file_name)

    if not output_path.exists() or not output_path.is_file():
        raise HTTPException(status_code=404, detail="Generated file not found")

    if not _is_editable_output(output_path):
        raise HTTPException(
            status_code=400,
            detail="Only DOCX, PPTX, and XLSX outputs can be active documents",
        )

    try:
        sandbox_backend = await asyncio.to_thread(get_backend, request.thread_id)
        await asyncio.to_thread(_upload_output_to_sandbox, sandbox_backend, output_path)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Could not prepare the generated file in the active sandbox",
        ) from error

    current_document = WorkingDocument(
        filename=output_path.name,
        path=f"/workspace/output/{output_path.name}",
        file_type=output_path.suffix.lower().lstrip("."),
    )
    set_current_document(request.thread_id, current_document)

    return {
        "message": "Generated file is now the active document",
        "active_output": {
            "file_name": current_document.filename,
            "file_type": current_document.file_type,
        },
    }


@router.delete("/outputs/active")
async def clear_active_output(thread_id: str):
    """Deselect the active working document for this chat thread."""
    clear_current_document(thread_id)
    return {"message": "Active document cleared", "active_output": None}


@router.get("/outputs/{filename}/view")
async def view_output_file(filename: str):
    output_path = _resolve_output_file(filename)

    if not output_path.exists() or not output_path.is_file():
        raise HTTPException(status_code=404, detail="Generated file not found")

    return _output_file_response(output_path, disposition="inline")


@router.delete("/outputs/{filename}")
async def delete_output_file(filename: str):
    output_path = _resolve_output_file(filename)

    if not output_path.exists() or not output_path.is_file():
        raise HTTPException(status_code=404, detail="Generated file not found")

    try:
        output_path.unlink()
    except OSError as error:
        raise HTTPException(status_code=500, detail="Could not delete generated file") from error

    clear_current_document_for_filename(filename)

    return {"message": "Generated file deleted successfully"}


@router.get("/download/{filename}")
async def download_generated_file(filename: str):
    output_path = _resolve_output_file(filename)

    if not output_path.exists() or not output_path.is_file():
        raise HTTPException(status_code=404, detail="Generated file not found")

    return _output_file_response(output_path, disposition="attachment")


@router.get("/documents/{document_id}/metadata")
async def get_metadata(document_id: str):
    return {
        "metadata": get_saved_metadata(document_id),
        "domain": get_document_domain(document_id),
    }


@router.post("/documents/{document_id}/metadata")
async def save_document_metadata(document_id: str, request: DocumentMetadataUpdateRequest):
    metadata = save_metadata(document_id=document_id, metadata_dict=request.metadata)
    domain = None

    if request.domain_id is not None:
        domain_record = get_domain_by_id(request.domain_id)
        if not domain_record:
            raise HTTPException(status_code=404, detail="Domain not found")
        domain = assign_document_to_domain(document_id, request.domain_id, request.confidence)

    return {
        "message": "Document metadata saved",
        "metadata": metadata,
        "domain": domain,
    }


@router.post("/metadata/save")
async def save_metadata_endpoint(request: MetadataSaveRequest):
    metadata = save_metadata(
        document_id=request.document_id,
        metadata_dict=request.metadata
    )
    domain = None

    if request.domain_id is not None:
        domain_record = get_domain_by_id(request.domain_id)
        if not domain_record:
            raise HTTPException(status_code=404, detail="Domain not found")
        domain = assign_document_to_domain(request.document_id, request.domain_id, request.confidence)

    return {
        "message": "Document metadata saved",
        "metadata": metadata,
        "domain": domain,
    }


@router.get("/domains")

async def list_domains():
    return {"domains": get_all_domains()}

@router.get("/domains/{domain_id}/documents")
async def get_domain_documents(domain_id: str):
    # Handle special "unorganized" case
    if domain_id == "unorganized":
        documents = get_unorganized_documents()
        return {
            "domain": {
                "id": "unorganized",
                "name": "Unorganized Files",
                "description": "Documents without semantic domain assignment",
                "created_date": None,
            },
            "documents": documents,
        }

    # Handle regular numeric domain IDs
    try:
        domain_id_int = int(domain_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID")

    domain = get_domain_by_id(domain_id_int)

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    documents = get_documents_by_domain(domain_id_int)

    return {
        "domain": domain,
        "documents": documents,
    }

@router.post("/domains")
async def create_new_domain(request: DomainCreateRequest):
    try:
        domain = create_domain(request.name, request.description)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Domain already exists")

    return {
        "message": "Domain created",
        "domain": domain,
    }


@router.put("/domains/{domain_id}")
async def update_existing_domain(domain_id: int, request: DomainUpdateRequest):
    try:
        domain = update_domain(domain_id, request.name, request.description)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Domain already exists")

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    return {
        "message": "Domain updated",
        "domain": domain,
    }


@router.delete("/domains/{domain_id}")
async def delete_existing_domain(domain_id: int):
    deleted = delete_domain(domain_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Domain not found")

    return {
        "message": "Domain deleted. Documents were moved to Unorganized Files.",
    }


@router.post("/generate-presentation")
async def generate_presentation(request: PresentationGenerationRequest):
    """Deprecated: prevents the legacy title-and-text PPTX generator bypass."""
    result = OfficeDocumentService.create_presentation(
        title=request.title,
        slides=request.slides,
    )
    raise HTTPException(status_code=409, detail=result["message"])
