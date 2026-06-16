from modal_sandbox.sandbox import analyze_file

# future imports
# from modal_sandbox.officecli import run_officecli
# from modal_sandbox.officecli import generate_ppt
# from modal_sandbox.officecli import generate_docx


class SandboxService:

    @staticmethod
    def analyze_file(file_bytes: bytes):
        return analyze_file.remote(file_bytes)

    # Placeholder for next step
    @staticmethod
    def execute_officecli(task: dict):
        raise NotImplementedError("OfficeCLI not connected yet")


sandbox_service = SandboxService()