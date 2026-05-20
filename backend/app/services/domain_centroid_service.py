import json
import numpy as np
from typing import Optional

from app.db.database import get_connection
from app.services.document_centroid_service import (
    get_document_centroid,
)
from app.services.vector_service import embeddings


def _domain_semantic_embedding(name: str, description: Optional[str]):
    embedding_input = name.strip()

    if description:
        embedding_input += f" {description.strip()}"

    if not embedding_input:
        return None

    return embeddings.embed_query(embedding_input)


def recompute_domain_centroid(domain_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, description FROM domains WHERE id = ?",
        (domain_id,)
    )
    domain = cursor.fetchone()

    if not domain:
        conn.close()
        return None

    semantic_embedding = _domain_semantic_embedding(
        domain["name"],
        domain["description"]
    )

    # Get all documents assigned to this domain
    cursor.execute(
        """
        SELECT document_id
        FROM document_domains
        WHERE domain_id = ?
        """,
        (domain_id,)
    )

    rows = cursor.fetchall()

    document_centroids = []

    for row in rows:
        document_id = row["document_id"]

        centroid = get_document_centroid(document_id)

        if centroid:
            document_centroids.append(centroid)

    centroid_inputs = []

    if semantic_embedding:
        centroid_inputs.append(semantic_embedding)

    centroid_inputs.extend(document_centroids)

    if not centroid_inputs:
        conn.close()
        return None

    # Average the domain description embedding with all assigned document centroids.
    domain_centroid = np.mean(
        np.array(centroid_inputs),
        axis=0
    )

    serialized_embedding = json.dumps(
        domain_centroid.tolist()
    )

    # Update domain embedding
    cursor.execute(
        """
        UPDATE domains
        SET embedding = ?
        WHERE id = ?
        """,
        (serialized_embedding, domain_id)
    )

    conn.commit()
    conn.close()

    return domain_centroid.tolist()
