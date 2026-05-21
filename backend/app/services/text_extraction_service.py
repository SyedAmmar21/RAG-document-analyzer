from pathlib import Path
from pypdf import PdfReader
from docx import Document
from app.core.paths import resolve_storage_path


def extract_text(file_path: str) -> str:
    """
    Extract text from a document file.
    
    Args:
        file_path: Path to the file (can be absolute or relative)
    
    Returns:
        Extracted text content
    """
    # Ensure we have an absolute path
    absolute_path = resolve_storage_path(file_path) if not Path(file_path).is_absolute() else Path(file_path)
    
    ext = absolute_path.suffix.lower()

    if ext == ".txt":
        return extract_txt(str(absolute_path))

    elif ext == ".pdf":
        return extract_pdf(str(absolute_path))

    elif ext == ".docx":
        return extract_docx(str(absolute_path))

    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ---------- TXT ----------
def extract_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


# ---------- PDF ----------
def extract_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    return text.strip()


# ---------- DOCX ----------
def extract_docx(file_path: str) -> str:
    doc = Document(file_path)
    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text.strip()