import modal

image = (
    modal.Image.debian_slim()
    .pip_install("reportlab")
)

app = modal.App("rag-document-sandbox")


@app.function(image=image)
def execute_task(
    task_type: str,
    content: str
):
    if task_type != "pdf":
        return {
            "status": "unsupported"
        }

    from reportlab.pdfgen import canvas

    filename = "report.pdf"

    c = canvas.Canvas(filename)

    c.drawString(
        100,
        750,
        content[:100]
    )

    c.save()

    with open(filename, "rb") as f:
        pdf_bytes = f.read()

    return {
        "status": "success",
        "filename": filename,
        "pdf_bytes": pdf_bytes
    }


@app.local_entrypoint()
def main():
    result = execute_task.remote(
        task_type="pdf",
        content="Gold outlook report generated from sandbox"
    )

    print(
        result["status"],
        result["filename"],
        len(result["pdf_bytes"])
    )