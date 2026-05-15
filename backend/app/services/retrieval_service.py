from elasticsearch import Elasticsearch
from networkx import hits
from app.core.config import ELASTICSEARCH_HOST
from langchain_openai import OpenAIEmbeddings

# Elasticsearch connection
es = Elasticsearch(
    ELASTICSEARCH_HOST,
    request_timeout=30,
    verify_certs=False
)

# OpenAI embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


# knn search
def search_documents(
    query: str,
    document_id: str | None = None,
    document_ids: list[str] | None = None,
    top_k: int = 8
):
    # Embed query
    query_vector = embeddings.embed_query(query)

    # Base kNN query
    knn_query = {
        "knn": {
            "field": "embedding",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": top_k * 8,
        }
    }

    # SINGLE document retrieval
    if document_id:
        knn_query["knn"]["filter"] = {
            "term": {
                "document_id": document_id
            }
        }

    # MULTI-document retrieval
    elif document_ids:
        knn_query["knn"]["filter"] = {
            "terms": {
                "document_id": document_ids
            }
        }

    response = es.search(
        index="documents",
        body=knn_query
    )

    hits = response["hits"]["hits"]

    # Extract structured results

    results = []

    for hit in hits:
        source = hit["_source"]

        results.append({
            "document_id": source.get("document_id"),
            "document_name": source.get("document_name", "Unknown Document"),
            "text": source.get("text", ""),
            "score": hit.get("_score", 0)
        })

    return results