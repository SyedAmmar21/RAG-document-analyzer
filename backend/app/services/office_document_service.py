from app.services.sandbox_service import run_sandbox


class OfficeDocumentService:

    @staticmethod
    def create_presentation(
        title: str,
        slides: list[str]
    ):
        """
        Generate a PowerPoint presentation through
        the Modal OfficeCLI sandbox.
        """

        payload = {
            "action": "create_presentation",
            "title": title,
            "slides": slides,
        }

        result = run_sandbox(payload)

        return result