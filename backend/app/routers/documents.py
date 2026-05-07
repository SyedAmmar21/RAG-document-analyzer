import os
from typing import Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import ELASTICSEARCH_HOST
from app.db.database import get_connection
from app.services.document_service import get_document_metadata, save_document_metadata

router = APIRouter()

es = Elasticsearch(
    ELASTICSEARCH_HOST,
    request_timeout=30,
    verify_certs=False
)


class DocumentMetadataRequest(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None


@router.get("/documents")
async def get_documents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT rowid AS number, id, file_path, created_date
    FROM documents
    ORDER BY created_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    documents = [
        {
            "number": row["number"],
            "document_id": row["id"],
            "file_name": os.path.basename(row["file_path"]),
            "file_path": row["file_path"],
            "status": "ready",
            "created_date": row["created_date"],
        }
        for row in rows
    ]

    return {"documents": documents}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT file_path FROM documents WHERE id = ?",
        (document_id,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = row["file_path"]

    cursor.execute(
        "DELETE FROM document_metadata WHERE document_id = ?",
        (document_id,)
    )

    cursor.execute(
        "DELETE FROM documents WHERE id = ?",
        (document_id,)
    )
    conn.commit()
    conn.close()

    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    es.delete_by_query(
        index="documents",
        body={
            "query": {
                "term": {
                    "document_id": document_id
                }
            }
        },
        conflicts="proceed",
        refresh=True,
    )

    return {"message": "Document deleted successfully"}


@router.get("/documents/{document_id}/metadata")
async def get_metadata(document_id: str):
    return {"metadata": get_document_metadata(document_id)}


@router.post("/documents/{document_id}/metadata")
async def save_metadata(document_id: str, request: DocumentMetadataRequest):
    metadata = save_document_metadata(
        document_id=document_id,
        metadata={
            "name": request.name,
            "location": request.location,
            "date": request.date,
        }
    )

    return {
        "message": "Document metadata saved",
        "metadata": metadata
    }
