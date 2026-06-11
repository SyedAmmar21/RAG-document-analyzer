from modal_sandbox.sandbox import execute_task


def generate_pdf_report(content: str):
    result = execute_task.remote(
        task_type="pdf",
        content=content
    )

    return result