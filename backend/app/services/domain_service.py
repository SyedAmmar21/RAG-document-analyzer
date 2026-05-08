from datetime import datetime, timezone, timedelta
from typing import Optional

from app.db.database import get_connection

MALAYSIA_TZ = timezone(timedelta(hours=8))


def get_all_domains():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, description, created_date
    FROM domains
    ORDER BY name ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "created_date": row["created_date"],
        }
        for row in rows
    ]


def create_domain(name: str, description: Optional[str] = None):
    clean_name = name.strip()
    clean_description = description.strip() if description else None

    if not clean_name:
        raise ValueError("Domain name is required.")

    conn = get_connection()
    cursor = conn.cursor()
    created_date = datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")

    cursor.execute(
        "INSERT INTO domains (name, description, created_date) VALUES (?, ?, ?)",
        (clean_name, clean_description, created_date)
    )
    domain_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return get_domain_by_id(domain_id)


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
