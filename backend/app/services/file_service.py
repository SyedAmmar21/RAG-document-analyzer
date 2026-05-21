import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import MAX_FILE_SIZE
from app.core.paths import UPLOAD_DIR, to_relative_storage_path, ensure_directories_exist

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def validate_file_type(file: UploadFile):
    filename = file.filename.lower()

    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Invalid file type")


def validate_file_size(file: UploadFile):
    file.file.seek(0, 2)  # move to end
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 5MB limit")


def save_file(file: UploadFile) -> str:
    """
    Save an uploaded file to UPLOAD_DIR and return its relative storage path.
    
    Args:
        file: The UploadFile from FastAPI
        
    Returns:
        Relative path suitable for database storage (e.g., "uploads/file_123.pdf")
    """
    ensure_directories_exist()

    original_name = file.filename
    name, ext = Path(original_name).stem, Path(original_name).suffix

    # Use UUID to ensure unique filenames and avoid collisions
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    absolute_path = UPLOAD_DIR / unique_filename

    # Save file
    with open(absolute_path, "wb") as f:
        f.write(file.file.read())

    # Return relative path for database storage
    relative_path = to_relative_storage_path(absolute_path)
    return relative_path

