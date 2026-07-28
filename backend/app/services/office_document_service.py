from pathlib import Path
from uuid import uuid4

from app.core.paths import OUTPUT_DIR, ensure_directories_exist
from app.services.sandbox_service import run_sandbox


class OfficeDocumentService:
    """
    Generic document export service for non-PowerPoint deliverables.

    PPTX is deliberately excluded from this generic payload path. A title plus
    a list of strings has no visual contract, so routing it to a sandbox
    generator inevitably creates title-and-text slides and bypasses the
    DeepAgent presentation workflow.
    """

    SUPPORTED_DOCUMENT_TYPES = {
        "pptx",
        "docx",
        "xlsx",
        "pdf",
    }

    @staticmethod
    def export_document(
        document_type: str,
        content: dict,
    ):
        """
        Export a generated document through the shared sandbox pipeline.

        `content` is intentionally generic so future agent flows can pass
        structured reasoning output without adding separate services or routes
        per document type.
        """

        normalized_document_type = document_type.lower()

        if normalized_document_type not in OfficeDocumentService.SUPPORTED_DOCUMENT_TYPES:
            return {
                "status": "error",
                "message": f"Unsupported document type: {document_type}",
            }

        if normalized_document_type == "pptx":
            return {
                "status": "error",
                "message": (
                    "PPTX generation must use the DeepAgent presentation workflow "
                    "(plan, official recipe selection, generation, QA). The generic "
                    "export payload cannot represent a professional slide contract."
                ),
            }

        payload = {
            "action": "export_document",
            "document_type": normalized_document_type,
            "content": content,
        }

        result = run_sandbox(payload)

        if result["status"] != "success":
            return result

        return OfficeDocumentService._persist_generated_file(
            document_type=normalized_document_type,
            file_bytes=result["file_bytes"],
        )

    @staticmethod
    def create_presentation(
        title: str,
        slides: list[str]
    ):
        """
        Deprecated adapter retained only to give legacy callers an explicit,
        actionable failure instead of silently producing simplistic slides.
        """

        return {
            "status": "error",
            "message": (
                "This legacy presentation API accepts only a title and strings, "
                "so it cannot produce a planned professional deck. Use /query and "
                "the DeepAgent presentation workflow instead."
            ),
        }

    @staticmethod
    def _persist_generated_file(
        document_type: str,
        file_bytes: bytes,
    ):
        """
        Persist generated files using the existing storage/outputs contract.

        We keep UUID-based filenames and the existing download endpoint shape
        so frontend integration can stay simple while new formats are added.
        """

        ensure_directories_exist()

        filename = f"{uuid4()}.{document_type}"
        file_path = Path(OUTPUT_DIR) / filename

        with open(file_path, "wb") as file_handle:
            file_handle.write(file_bytes)

        return {
            "status": "success",
            "filename": filename,
            "file_path": str(file_path),
            "download_url": f"/download/{filename}",
            "document_type": document_type,
        }
