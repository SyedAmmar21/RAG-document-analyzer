from pathlib import Path
from uuid import uuid4

from app.core.paths import OUTPUT_DIR, ensure_directories_exist
from app.services.sandbox_service import run_sandbox


class OfficeDocumentService:
    """
    Generic document export service for agent-generated deliverables.

    The project has outgrown a PPT-only export path. This service now exposes
    a generic export entry point that the Deep Agent can eventually call after
    producing research output, while keeping the existing presentation helper
    alive as a backwards-compatible adapter.
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
        Temporary backwards-compatible PPT adapter.

        Existing routers, tools, and clients still call this method today.
        Internally it now routes into the generic export pipeline so the
        architecture can evolve without breaking the current API.
        """

        return OfficeDocumentService.export_document(
            document_type="pptx",
            content={
                "title": title,
                "slides": slides,
            },
        )

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
