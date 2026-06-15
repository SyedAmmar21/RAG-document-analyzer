import os
import modal
from openai import OpenAI


app = modal.App("sandbox-learning")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "openai",
        "reportlab"
    )
)

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("openai-secret")
    ]
)
def analyze_file(file_bytes: bytes):

    from openai import OpenAI
    import os
    import tempfile
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    text = file_bytes.decode("utf-8")

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"]
    )

    response = client.responses.create(
        model="gpt-4.1-nano",
        input=f"""
Create a professional report about this laptop inventory.

Document:

{text}
"""
    )

    report_text = response.output_text

    pdf_path = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    ).name

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    content = [
        Paragraph(
            report_text.replace("\n", "<br/>"),
            styles["BodyText"]
        )
    ]

    doc.build(content)

    with open(pdf_path, "rb") as f:
        return f.read()
    
@app.local_entrypoint()
def main():

    with open(
        r"C:\Users\USER\Downloads\note.txt",
        "rb"
    ) as f:
        file_bytes = f.read()

    pdf_bytes = analyze_file.remote(
        file_bytes
    )

    with open(
        r"C:\Users\USER\Downloads\laptop_report.pdf",
        "wb"
    ) as f:
        f.write(pdf_bytes)

    print("PDF saved.")