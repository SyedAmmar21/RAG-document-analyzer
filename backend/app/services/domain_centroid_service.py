import json
import numpy as np

from app.db.database import get_connection
from app.services.document_centroid_service import (
    get_document_centroid,
)


def recompute_domain_centroid(domain_id: int):
    conn = get_connection()
    cursor = conn.cursor()

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

    if not rows:
        conn.close()
        return None

    document_centroids = []

    for row in rows:
        document_id = row["document_id"]

        centroid = get_document_centroid(document_id)

        if centroid:
            document_centroids.append(centroid)

    if not document_centroids:
        conn.close()
        return None

    # Average all document centroids
    domain_centroid = np.mean(
        np.array(document_centroids),
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