from urllib import request

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.rag_agent_service import get_rag_agent
from app.services.document_service import add_ai_response
from app.services.domain_service import get_documents_by_domain

from app.services.news_ingestion_service import search_gold_news
from app.services.news_ingestion_service import extract_article_text
from app.services.news_ingestion_service import save_article_as_txt

router = APIRouter()


# Request schema
from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str

    # OLD compatibility field
    document_id: Optional[str] = None

    # NEW retrieval scope architecture
    scope_type: str = "global"

    folder_ids: list[str|int] = []

    document_ids: list[str] = []

class FieldSearchRequest(BaseModel):
    fields: list[str]
    document_id: str

# Endpoint
@router.post("/query")
async def query_agent(request: QueryRequest):
    # GLOBAL mode
    if request.scope_type == "global":
        agent = get_rag_agent()

    # FOLDER mode
    elif request.scope_type == "folders":
        all_document_ids = []

        for folder_id in request.folder_ids:

            print("PROCESSING FOLDER:", folder_id)

            # Handle synthetic unorganized folder
            if str(folder_id) == "unorganized":

                from app.services.domain_service import get_unorganized_documents

                documents = get_unorganized_documents()

                for document in documents:
                    document_id = document["document_id"]

                    if document_id not in all_document_ids:
                         all_document_ids.append(document_id)

                continue

            try:
                documents = get_documents_by_domain(
                    int(folder_id)
                )


                for document in documents:
                    document_id = document["document_id"]

                    if document_id not in all_document_ids:
                        all_document_ids.append(document_id)

            except Exception as e:
                print("FOLDER ERROR:", e)


        agent = get_rag_agent(
            document_ids=all_document_ids
        )

    # DOCUMENT mode
    elif request.scope_type == "documents":
        agent = get_rag_agent(
            document_ids=request.document_ids
        )

    # FALLBACK single-document compatibility
    else:
        agent = get_rag_agent(
            document_id=request.document_id
        )

    # Run agent
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": request.query}
        ]
    })

    # Extract answer
    answer = response["messages"][-1].content

    #  SAVE AI RESPONSE INTO DB
    add_ai_response(
        document_id=request.document_id,
        query=request.query,
        response=answer
    )
    
    # Return response
    return {
        "answer": answer
    }


@router.post("/field-search")
async def field_search(request: FieldSearchRequest):
    fields = [field.strip() for field in request.fields if field.strip()]

    if not fields:
        return {
            "answer": "Add at least one field or search key to extract from the document."
        }

    agent = get_rag_agent(request.document_id)
    fields_text = "\n".join(f"- {field}" for field in fields)

    prompt = f"""
Extract the following requested fields/search keys from the uploaded document:

{fields_text}

Return the answer in Markdown using this structure:

## Extracted Fields
| Field | Value Found | Evidence / Notes |
| --- | --- | --- |

Rules:
- Use the retrieval tools to search the uploaded document.
- Base every value only on retrieved document content.
- If a field is not found, write "Not found" and explain briefly.
- Keep the response concise and structured.
"""

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })

    answer = response["messages"][-1].content

    add_ai_response(
        document_id=request.document_id,
        query=f"Field search: {', '.join(fields)}",
        response=answer
    )

    return {
        "answer": answer
    }

@router.get("/test-news")
def test_news():

    results = search_gold_news()

    return results

@router.get("/test-extract")
def test_extract():

    url = "https://markets.businessinsider.com/news/stocks/iux-publishes-gold-market-insight-on-volatility-trends-and-user-engagement-in-2026-1036148744"

    text = extract_article_text(url)

    return {
        "length": len(text) if text else 0,
        "preview": text[:3000] if text else None
    }

@router.get("/test-save-news")
def test_save_news():

    url = "https://markets.businessinsider.com/news/stocks/iux-publishes-gold-market-insight-on-volatility-trends-and-user-engagement-in-2026-1036148744"

    text = extract_article_text(url)

    path = save_article_as_txt(
        "gold_market_test",
        text
    )

    return {
        "saved_path": path,
        "text_length": len(text)
    }