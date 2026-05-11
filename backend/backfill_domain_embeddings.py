import json

from app.db.database import get_connection
from app.services.vector_service import embeddings


def backfill_domain_embeddings():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, description
        FROM domains
        WHERE embedding IS NULL
    """)

    domains = cursor.fetchall()

    print(f"Found {len(domains)} domains without embeddings.")

    for domain in domains:
        domain_id = domain["id"]
        name = domain["name"]
        description = domain["description"] or ""

        embedding_input = f"{name} {description}"

        print(f"Generating embedding for: {name}")

        domain_embedding = embeddings.embed_query(embedding_input)

        cursor.execute("""
            UPDATE domains
            SET embedding = ?
            WHERE id = ?
        """, (
            json.dumps(domain_embedding),
            domain_id
        ))

    conn.commit()
    conn.close()

    print("Backfill complete.")


if __name__ == "__main__":
    backfill_domain_embeddings()