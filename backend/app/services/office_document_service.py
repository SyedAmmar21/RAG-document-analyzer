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

        return run_sandbox(payload)