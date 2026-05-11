import numpy as np

from app.services.vector_service import embeddings
from app.services.document_centroid_service import (
    get_document_centroid,
)


def build_metadata_text(metadata: dict):
    parts = []

    title = metadata.get("title")
    focus = metadata.get("focus")

    if title:
        parts.append(title)

    if focus:
        parts.append(focus)

    for field in [
        "entities",
        "economic_indicators",
        "regions"
    ]:
        values = metadata.get(field, [])

        if values:
            parts.extend(values)

    return " ".join(parts)


def generate_hybrid_embedding(
    document_id: str,
    metadata: dict,
    metadata_weight: float = 0.7,
    chunk_weight: float = 0.3,
):
    # Generate metadata embedding
    metadata_text = build_metadata_text(metadata)

    metadata_embedding = embeddings.embed_query(
        metadata_text
    )

    # Generate chunk centroid
    chunk_centroid = get_document_centroid(
        document_id=document_id,
        max_chunks=5
    )

    # Fallback if no chunk centroid exists
    if not chunk_centroid:
        return metadata_embedding

    metadata_vector = np.array(metadata_embedding)
    chunk_vector = np.array(chunk_centroid)

    hybrid_vector = (
        metadata_vector * metadata_weight
        +
        chunk_vector * chunk_weight
    )

    return hybrid_vector.tolist()
