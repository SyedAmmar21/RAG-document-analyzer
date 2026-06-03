import json
import numpy as np

from app.db.database import get_connection


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    denominator = np.linalg.norm(vec1) * np.linalg.norm(vec2)

    if denominator == 0:
        return 0.0

    similarity = np.dot(vec1, vec2) / denominator

    return float(similarity)


def get_best_matching_domain(document_embedding):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, embedding
        FROM domains
        WHERE embedding IS NOT NULL
    """)

    domains = cursor.fetchall()

    conn.close()

    if not domains:
        return None

    best_domain = None
    highest_similarity = -1

    for domain in domains:
        domain_embedding = json.loads(domain["embedding"])

        similarity = cosine_similarity(
            document_embedding,
            domain_embedding
        )
        print(domain["name"],round(similarity, 4))

        if similarity > highest_similarity:
            highest_similarity = similarity

            best_domain = {
                "id": domain["id"],
                "name": domain["name"],
                "similarity": round(similarity, 4)
            }

    return best_domain