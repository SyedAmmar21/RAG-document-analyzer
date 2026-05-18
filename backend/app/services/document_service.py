import uuid
import json
import os
import re
from datetime import datetime, timezone, timedelta
from app.db.database import get_connection

MALAYSIA_TZ = timezone(timedelta(hours=8))


def create_document_record(file_path: str, file_size: int, file_type: str):
    conn = get_connection()
    cursor = conn.cursor()

    document_id = str(uuid.uuid4())
    created_date = datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")

    metadata = {
        "file_size": file_size,
        "file_type": file_type,
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
    name, ext = os.path.splitext(filename)
    expected_pattern = re.compile(
        rf"^{re.escape(name)}_edited(?:_\d+)?{re.escape(ext)}$",
        re.IGNORECASE
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT rowid AS number, id, created_date, file_path
    FROM documents
    ORDER BY created_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        file_name = os.path.basename(row["file_path"])
        if expected_pattern.match(file_name):
            return {
                "number": row["number"],
                "document_id": row["id"],
                "file_name": file_name,
                "file_path": row["file_path"],
                "created_date": row["created_date"],
            }

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

    return {
        "document_id": row["id"],
        "file_path": row["file_path"],
        "file_name": os.path.basename(row["file_path"]),
        "created_date": row["created_date"],
    }