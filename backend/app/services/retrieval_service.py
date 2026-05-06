from elasticsearch import Elasticsearch
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


#knn search
def search_documents(query: str, document_id: str, top_k: int = 8):
    # Embed query
    query_vector = embeddings.embed_query(query)

    # kNN query
    knn_query = {
        "knn": {
            "field": "embedding",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": top_k * 8,
            "filter": {
                "term": {
                    "document_id": document_id
                }
            }
        }
    }

    response = es.search(index="documents", body=knn_query)

    hits = response["hits"]["hits"]

    # Extract results
    results = [hit["_source"]["text"] for hit in hits]

    return results
