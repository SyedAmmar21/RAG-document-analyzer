from elasticsearch import Elasticsearch
from app.core.config import ELASTICSEARCH_HOST
from langchain_openai import OpenAIEmbeddings
import os

ELASTICSEARCH_HOST = os.getenv(
    "ELASTICSEARCH_HOST",
    "http://elasticsearch:9200"
)

es = Elasticsearch(
    ELASTICSEARCH_HOST,
    request_timeout=30,
    verify_certs=False
)


def check_connection():
    try:
        response = es.info()
        return response
    except Exception as e:
        print("Connection error:", e)
        return None

#create index
def create_index():
    index_name = "documents"

    if es.indices.exists(index=index_name):
        print("Index already exists")
        return

    mapping = {
        "mappings": {
            "properties": {
                "document_id": {"type": "keyword"},
                "text": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 1536, 
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

    es.indices.create(index=index_name, body=mapping)
    print("Index created successfully")

#generate embedding
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


# chunking text
def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# index docs
def index_document(document_id: str, text: str):
    chunks = chunk_text(text)

    for chunk in chunks:
        embedding = embeddings.embed_query(chunk)

        doc = {
            "document_id": document_id,
            "text": chunk,
            "embedding": embedding
        }

        es.index(index="documents", document=doc)
        