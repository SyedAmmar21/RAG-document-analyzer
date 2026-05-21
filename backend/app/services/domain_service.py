from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path
from app.db.database import get_connection
import json
from app.services.vector_service import embeddings

from app.services.domain_centroid_service import (
    recompute_domain_centroid,
)

MALAYSIA_TZ = timezone(timedelta(hours=8))


def get_all_domains():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
SELECT
    d.id,
    d.name,
    d.description,
    d.created_date,
    COUNT(dd.document_id) AS document_count
FROM domains d
LEFT JOIN document_domains dd
    ON d.id = dd.domain_id
GROUP BY d.id
ORDER BY d.name ASC
""")
    rows = cursor.fetchall()
    conn.close()

    domains = [
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "created_date": row["created_date"],
            "document_count": row["document_count"],
        }
        for row in rows
    ]

    # Add "Unorganized Files" as a synthetic fallback folder
    unorganized_count = count_unorganized_documents()
    if unorganized_count > 0:
        domains.append({
            "id": "unorganized",
            "name": "Unorganized Files",
            "description": "Documents without semantic domain assignment",
            "created_date": None,
            "document_count": unorganized_count,
        })

    return domains


def create_domain(name: str, description: Optional[str] = None):
    clean_name = name.strip()
    clean_description = description.strip() if description else None

    if not clean_name:
        raise ValueError("Domain name is required.")

    # Combine semantic context
    embedding_input = clean_name

    if clean_description:
        embedding_input += f" {clean_description}"

    # Generate embedding
    domain_embedding = embeddings.embed_query(embedding_input)

    conn = get_connection()
    cursor = conn.cursor()

    created_date = datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")

    cursor.execute(
        """
        INSERT INTO domains (
            name,
            description,
            embedding,
            created_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            clean_name,
            clean_description,
            json.dumps(domain_embedding),
            created_date
        )
    )

    domain_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return get_domain_by_id(domain_id)


def update_domain(domain_id: int, name: str, description: Optional[str] = None):
    clean_name = name.strip()
    clean_description = description.strip() if description else None

    if not clean_name:
        raise ValueError("Domain name is required.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE domains
            SET name = ?, description = ?
            WHERE id = ?
            """,
            (clean_name, clean_description, domain_id)
        )

        if cursor.rowcount == 0:
            conn.close()
            return None

        conn.commit()
    except Exception:
        conn.close()
        raise

    conn.close()

    recompute_domain_centroid(domain_id)

    return get_domain_by_id(domain_id)


def delete_domain(domain_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM domains WHERE id = ?",
        (domain_id,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    cursor.execute(
        "DELETE FROM document_domains WHERE domain_id = ?",
        (domain_id,)
    )
    cursor.execute(
        "DELETE FROM domains WHERE id = ?",
        (domain_id,)
    )

    conn.commit()
    conn.close()

    return True


def get_domain_by_id(domain_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, description, created_date FROM domains WHERE id = ?",
        (domain_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "created_date": row["created_date"],
    }


def get_domain_by_name(name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, description, created_date FROM domains WHERE LOWER(name) = LOWER(?)",
        (name,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "created_date": row["created_date"],
    }


def assign_document_to_domain(document_id: str, domain_id: int, confidence: Optional[float] = None):
    conn = get_connection()
    cursor = conn.cursor()
    created_date = datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")

    cursor.execute(
        "DELETE FROM document_domains WHERE document_id = ?",
        (document_id,)
    )
    cursor.execute(
        """
        INSERT INTO document_domains (document_id, domain_id, confidence, created_date)
        VALUES (?, ?, ?, ?)
        """,
        (document_id, domain_id, confidence, created_date)
    )

    conn.commit()
    conn.close()

    # Recompute adaptive semantic centroid
    recompute_domain_centroid(domain_id)

    return get_document_domain(document_id)


def get_document_domain(document_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            dd.id,
            dd.document_id,
            dd.domain_id,
            dd.confidence,
            dd.created_date,
            d.name,
            d.description
        FROM document_domains dd
        JOIN domains d ON d.id = dd.domain_id
        WHERE dd.document_id = ?
        ORDER BY dd.created_date DESC
        LIMIT 1
        """,
        (document_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "document_id": row["document_id"],
        "domain_id": row["domain_id"],
        "domain_name": row["name"],
        "description": row["description"],
        "confidence": row["confidence"],
        "created_date": row["created_date"],
    }

def get_documents_by_domain(domain_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        d.id,
        d.file_path,
        d.created_date
    FROM document_domains dd
    JOIN documents d
        ON d.id = dd.document_id
    WHERE dd.domain_id = ?
    ORDER BY d.created_date DESC
    """, (domain_id,))

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "document_id": row["id"],
            "file_name": Path(row["file_path"]).name,
            "file_path": row["file_path"],
            "created_date": row["created_date"],
        }
        for row in rows
    ]


def get_unorganized_documents():
    """
    Get all documents that do NOT have a domain assignment.
    These are documents without an entry in the document_domains table.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        d.id,
        d.file_path,
        d.created_date
    FROM documents d
    WHERE d.id NOT IN (
        SELECT DISTINCT document_id FROM document_domains
    )
    ORDER BY d.created_date DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "document_id": row["id"],
            "file_name": Path(row["file_path"]).name,
            "file_path": row["file_path"],
            "created_date": row["created_date"],
        }
        for row in rows
    ]


def count_unorganized_documents():
    """Count documents without domain assignments."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) as count FROM documents d
    WHERE d.id NOT IN (
        SELECT DISTINCT document_id FROM document_domains
    )
    """)

    row = cursor.fetchone()
    conn.close()

    return row["count"] if row else 0
