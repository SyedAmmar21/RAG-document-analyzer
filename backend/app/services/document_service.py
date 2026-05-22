import uuid
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from app.db.database import get_connection
from app.core.paths import resolve_storage_path, to_relative_storage_path

import sqlite3
from app.db.database import DB_PATH

MALAYSIA_TZ = timezone(timedelta(hours=8))


def create_document_record(file_path: str, file_size: int, file_type: str, original_filename: str = None):
    """
    Create a new document record in the database.
    
    Args:
        file_path: Relative path to the file (e.g., "uploads/file.pdf")
        file_size: File size in bytes
        file_type: File extension/type (e.g., "pdf")
        original_filename: Original filename for duplicate detection
    """
    conn = get_connection()
    cursor = conn.cursor()

    document_id = str(uuid.uuid4())
    created_date = datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")

    metadata = {
        "file_size": file_size,
        "file_type": file_type,
        "original_filename": original_filename,
        "ai_responses": []
    }

    cursor.execute("""
    INSERT INTO documents (id, created_date, file_path, meta_json)
    VALUES (?, ?, ?, ?)
    """, (
        document_id,
        created_date,
        file_path,
        json.dumps(metadata)
    ))

    conn.commit()
    conn.close()

    return document_id


def find_document_by_upload_name(filename: str):
    """
    Find an existing document by original filename (for duplicate detection).
    
    This searches through metadata to find a document with the same original filename.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT rowid AS number, id, created_date, file_path, meta_json
    FROM documents
    ORDER BY created_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        try:
            metadata = json.loads(row["meta_json"])
            original_filename = metadata.get("original_filename", "")
            
            # Match by original filename
            if original_filename and original_filename.lower() == filename.lower():
                stored_path = row["file_path"]
                # Extract just the filename from stored path
                file_name = Path(stored_path).name
                
                return {
                    "number": row["number"],
                    "document_id": row["id"],
                    "file_name": file_name,
                    "file_path": stored_path,
                    "created_date": row["created_date"],
                }
        except (json.JSONDecodeError, KeyError):
            continue

    return None



# ADD AI RESPONSE
def add_ai_response(document_id: str, query: str, response: str):
    conn = get_connection()
    cursor = conn.cursor()

    # 🔍 Get current metadata
    cursor.execute(
        "SELECT meta_json FROM documents WHERE id = ?",
        (document_id,)
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return

    metadata = json.loads(row[0])

    # Ensure key exists
    if "ai_responses" not in metadata:
        metadata["ai_responses"] = []

    #  Append new response
    metadata["ai_responses"].append({
        "query": query,
        "response": response,
        "timestamp": datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")
    })

    # Update DB
    cursor.execute(
        "UPDATE documents SET meta_json = ? WHERE id = ?",
        (json.dumps(metadata), document_id)
    )

    conn.commit()
    conn.close()


def get_document_by_id(document_id: str):
    """Get document by ID and return with relative path."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, file_path, created_date
    FROM documents
    WHERE id = ?
    """, (document_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    # Extract filename from relative path
    file_name = Path(row["file_path"]).name
    
    return {
        "document_id": row["id"],
        "file_path": row["file_path"],
        "file_name": file_name,
        "created_date": row["created_date"],
    }

def get_all_documents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM documents
    """)

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]