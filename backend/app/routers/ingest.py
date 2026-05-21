from fastapi import APIRouter, UploadFile, File
import logging
from pathlib import Path

from app.services.file_service import (
    validate_file_type,
    validate_file_size,
    save_file
)
from app.services.document_service import (
    find_document_by_upload_name,
)
from app.services.domain_service import get_document_domain
from app.services.metadata_service import get_metadata_values
from app.services.document_ingestion_service import process_document_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    """Handle file upload, validation, and document ingestion."""
    # Validate file
    validate_file_type(file)
    validate_file_size(file)

    # Check for duplicates
    existing_document = find_document_by_upload_name(file.filename)
    if existing_document:
        return {
            "message": f"This file is already in the repository at document number {existing_document['number']}. Reusing the existing document.",
            "document_id": existing_document["document_id"],
            "file_name": existing_document["file_name"],
            "file_path": existing_document["file_path"],
            "document_number": existing_document["number"],
            "is_duplicate": True,
            "metadata_suggestions": get_metadata_values(existing_document["document_id"]),
            "domain_suggestion": get_document_domain(existing_document["document_id"]),
        }

    # Save and ingest new file
    file_path = save_file(file)
    try:
        pipeline_result = process_document_pipeline(
            file_path=file_path,
            original_filename=file.filename
        )
    except Exception as error:
        logger.exception("File upload ingestion failed for %s", file.filename)
        raise

    return {
        "message": "File uploaded and indexed",
        "document_id": pipeline_result["document_id"],
        "file_name": Path(file_path).name,
        "file_path": file_path,
        "preview": pipeline_result["preview"],
        "metadata_suggestions": pipeline_result["metadata_suggestions"],
        "domain_suggestion": (
            pipeline_result["assigned_domain"]
            or pipeline_result["domain_suggestion"]
        ),
        "is_duplicate": False,
    }
