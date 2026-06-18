from pathlib import Path
from uuid import uuid4

from app.core.paths import OUTPUT_DIR
from app.services.sandbox_service import run_sandbox


class OfficeDocumentService:

    @staticmethod
    def create_presentation(
        title: str,
        slides: list[str]
    ):
        payload = {
            "action": "create_presentation",
            "title": title,
            "slides": slides
        }

        result = run_sandbox(payload)

        if result["status"] != "success":
            return result

        file_bytes = result["file_bytes"]

        filename = f"{uuid4()}.pptx"

        output_path = OUTPUT_DIR / filename

        with open(output_path, "wb") as f:
            f.write(file_bytes)

        return {
            "status": "success",
            "filename": filename,
            "file_path": str(output_path),
            "file_size": len(file_bytes)
        }