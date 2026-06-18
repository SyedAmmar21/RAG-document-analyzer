from pathlib import Path
from uuid import uuid4

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

        outputs_dir = Path("storage/outputs")
        outputs_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = f"{uuid4()}.pptx"

        file_path = outputs_dir / filename

        with open(file_path, "wb") as f:
            f.write(
                result["file_bytes"]
            )

        return {
            "status": "success",
            "filename": filename,
            "file_path": str(file_path)
        }