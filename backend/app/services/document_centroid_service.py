import numpy as np

from app.services.vector_service import es


def get_document_centroid(document_id: str, max_chunks: int = 5):
    response = es.search(
        index="documents",
        size=max_chunks,
        query={
            "term": {
                "document_id": document_id
            }
        }
    )

    hits = response["hits"]["hits"]

    if not hits:
        return None

    embeddings = []

    for hit in hits:
        source = hit["_source"]

        embedding = source.get("embedding")

        if embedding:
            embeddings.append(embedding)

    if not embeddings:
        return None

    centroid = np.mean(
        np.array(embeddings),
        axis=0
    )

    return centroid.tolist()