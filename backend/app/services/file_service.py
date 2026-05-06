import os
import uuid
from fastapi import UploadFile, HTTPException
from app.core.config import UPLOAD_DIR, MAX_FILE_SIZE

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


def save_file(file: UploadFile):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    original_name = file.filename
    name, ext = os.path.splitext(original_name)

    base_filename = f"{name}_edited{ext}"
    file_path = os.path.join(UPLOAD_DIR, base_filename)

    counter = 1

    # Handle duplicate names
    while os.path.exists(file_path):
        new_filename = f"{name}_edited_{counter}{ext}"
        file_path = os.path.join(UPLOAD_DIR, new_filename)
        counter += 1

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path
