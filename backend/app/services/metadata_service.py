from app.db.database import get_connection

METADATA_FIELDS = {
    "title",
    "published_date",
    "focus",
    "entities",
    "economic_indicators",
    "regions",
}

LIST_FIELDS = {
    "entities",
    "economic_indicators",
    "regions",
}


def _normalize_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None

    return str(value)


def validate_metadata(metadata_dict: dict):
    cleaned = {}

    for field in METADATA_FIELDS:
        value = metadata_dict.get(field)

        if field in LIST_FIELDS:
            if value is None:
                cleaned[field] = []
            elif isinstance(value, list):
                cleaned[field] = [
                    normalized
                    for normalized in (_normalize_value(item) for item in value)
                    if normalized
                ]
            else:
                normalized = _normalize_value(value)
                cleaned[field] = [normalized] if normalized else []
        else:
            cleaned[field] = _normalize_value(value)

    return cleaned


def save_metadata(document_id: str, metadata_dict: dict):
    metadata = validate_metadata(metadata_dict)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM document_metadata WHERE document_id = ?",
        (document_id,)
    )

    for field, value in metadata.items():
        if field in LIST_FIELDS:
            if not value:
                cursor.execute(
                    "INSERT INTO document_metadata (document_id, field, value) VALUES (?, ?, ?)",
                    (document_id, field, None)
                )
                continue

            for item in value:
                cursor.execute(
                    "INSERT INTO document_metadata (document_id, field, value) VALUES (?, ?, ?)",
                    (document_id, field, item)
                )
            continue

        cursor.execute(
            "INSERT INTO document_metadata (document_id, field, value) VALUES (?, ?, ?)",
            (document_id, field, value)
        )

    conn.commit()
    conn.close()

    return get_metadata(document_id)


def get_metadata(document_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT document_id, field, value FROM document_metadata WHERE document_id = ? ORDER BY rowid ASC",
        (document_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "document_id": row["document_id"],
            "field": row["field"],
            "value": row["value"],
        }
        for row in rows
    ]


def get_metadata_values(document_id: str):
    metadata = {
        "title": None,
        "published_date": None,
        "focus": None,
        "entities": [],
        "economic_indicators": [],
        "regions": [],
    }

    for row in get_metadata(document_id):
        field = row["field"]
        value = row["value"]

        if field in LIST_FIELDS:
            if value:
                metadata[field].append(value)
        elif field in metadata:
            metadata[field] = value

    return metadata
