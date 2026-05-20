import os
from sqlite3 import IntegrityError
from typing import Any, Dict, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import ELASTICSEARCH_HOST
from app.db.database import get_connection
from app.services.domain_service import (
    assign_document_to_domain,
    create_domain,
    get_all_domains,
    get_document_domain,
    get_domain_by_id,
    get_unorganized_documents,
)
from app.services.metadata_service import get_metadata as get_saved_metadata, save_metadata
from app.services.domain_service import get_documents_by_domain

router = APIRouter()

es = Elasticsearch(
    ELASTICSEARCH_HOST,
    request_timeout=30,
    verify_certs=False
)


class MetadataSaveRequest(BaseModel):
    document_id: str
    metadata: Dict[str, Any]
    domain_id: Optional[int] = None
    confidence: Optional[float] = None


class DocumentMetadataUpdateRequest(BaseModel):
    metadata: Dict[str, Any]
    domain_id: Optional[int] = None
    confidence: Optional[float] = None


class DomainCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


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

    document_ids = [row["id"] for row in rows]
    published_dates = {}

    if document_ids:
        placeholders = ",".join("?" for _ in document_ids)
        cursor.execute(
            f"""
            SELECT document_id, value
            FROM document_metadata
            WHERE field = 'published_date'
              AND document_id IN ({placeholders})
            """,
            document_ids,
        )

        published_dates = {
            row["document_id"]: row["value"]
            for row in cursor.fetchall()
            if row["value"]
        }

    conn.close()

    documents = [
        {
            "number": row["number"],
            "document_id": row["id"],
            "file_name": os.path.basename(row["file_path"]),
            "published_date": published_dates.get(row["id"]),
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
        "DELETE FROM document_domains WHERE document_id = ?",
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
    return {
        "metadata": get_saved_metadata(document_id),
        "domain": get_document_domain(document_id),
    }


@router.post("/documents/{document_id}/metadata")
async def save_document_metadata(document_id: str, request: DocumentMetadataUpdateRequest):
    metadata = save_metadata(document_id=document_id, metadata_dict=request.metadata)
    domain = None

    if request.domain_id is not None:
        domain_record = get_domain_by_id(request.domain_id)
        if not domain_record:
            raise HTTPException(status_code=404, detail="Domain not found")
        domain = assign_document_to_domain(document_id, request.domain_id, request.confidence)

    return {
        "message": "Document metadata saved",
        "metadata": metadata,
        "domain": domain,
    }


@router.post("/metadata/save")
async def save_metadata_endpoint(request: MetadataSaveRequest):
    metadata = save_metadata(
        document_id=request.document_id,
        metadata_dict=request.metadata
    )
    domain = None

    if request.domain_id is not None:
        domain_record = get_domain_by_id(request.domain_id)
        if not domain_record:
            raise HTTPException(status_code=404, detail="Domain not found")
        domain = assign_document_to_domain(request.document_id, request.domain_id, request.confidence)

    return {
        "message": "Document metadata saved",
        "metadata": metadata,
        "domain": domain,
    }


@router.get("/domains")

async def list_domains():
    return {"domains": get_all_domains()}

@router.get("/domains/{domain_id}/documents")
async def get_domain_documents(domain_id: str):
    # Handle special "unorganized" case
    if domain_id == "unorganized":
        documents = get_unorganized_documents()
        return {
            "domain": {
                "id": "unorganized",
                "name": "Unorganized Files",
                "description": "Documents without semantic domain assignment",
                "created_date": None,
            },
            "documents": documents,
        }

    # Handle regular numeric domain IDs
    try:
        domain_id_int = int(domain_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID")

    domain = get_domain_by_id(domain_id_int)

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    documents = get_documents_by_domain(domain_id_int)

    return {
        "domain": domain,
        "documents": documents,
    }

@router.post("/domains")
async def create_new_domain(request: DomainCreateRequest):
    try:
        domain = create_domain(request.name, request.description)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Domain already exists")

    return {
        "message": "Domain created",
        "domain": domain,
    }
