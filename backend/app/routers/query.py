from urllib import request
import logging
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.rag_agent_service import get_deep_rag_agent
from app.services.document_service import add_ai_response
from app.services.domain_service import get_documents_by_domain
from app.services.sandbox.session_store import get_backend

from app.services.news_ingestion_service import search_gold_news
from app.services.news_ingestion_service import extract_article_text
from app.services.news_ingestion_service import save_article_as_txt
from app.services.memory_service import (
    create_memory_entry,
    save_memory_entry
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Request schema
from typing import Optional
from pydantic import BaseModel
from uuid import uuid4


class QueryRequest(BaseModel):
    query: str

    # OLD compatibility field
    document_id: Optional[str] = None

    # NEW retrieval scope architecture
    scope_type: str = "global"

    folder_ids: list[str|int] = []

    document_ids: list[str] = []
    thread_id: str = "default"

class ReportRequest(BaseModel):
    query: str
    answer: str

class FieldSearchRequest(BaseModel):
    fields: list[str]
    document_id: str

# Endpoint
@router.post("/query")
async def query_agent(request: QueryRequest):
    # GLOBAL mode
    if request.scope_type == "global":
        agent = get_deep_rag_agent(thread_id=request.thread_id)

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


        agent = get_deep_rag_agent(
            document_ids=all_document_ids,
            thread_id=request.thread_id
        )

    # DOCUMENT mode
    elif request.scope_type == "documents":
        agent = get_deep_rag_agent(
            document_ids=request.document_ids,
            thread_id=request.thread_id
        )

    # FALLBACK single-document compatibility
    else:
        agent = get_deep_rag_agent(
            document_id=request.document_id,
            thread_id=request.thread_id
        )

    # Run agent with error handling
    try:
        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.query
                    }
                ]
            },

            config={
                # Recursion limit for multi-step planning with specialized tools.
                # Each tool call + reasoning step counts as 1 recursion iteration.
                "recursion_limit": 50,
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
        )

        # Post-invoke: download any files the agent generated in sandbox
        try:
            sandbox_backend = get_backend(request.thread_id)
            check = sandbox_backend.execute("ls /workspace/output/ 2>/dev/null")
            if check.exit_code == 0 and check.output.strip():
                filenames = [f.strip() for f in check.output.strip().split("\n") if f.strip()]
                downloaded_urls = []
                for filename in filenames:
                    results = sandbox_backend.download_files(
                        [f"/workspace/output/{filename}"]
                    )
                    if results and results[0].content is not None:
                        out_dir = Path("storage/outputs")
                        out_dir.mkdir(parents=True, exist_ok=True)
                        out_path = out_dir / filename
                        out_path.write_bytes(results[0].content)
                        downloaded_urls.append(f"/download/{filename}")
                        # Clear file from sandbox after download
                        sandbox_backend.execute(f"rm /workspace/output/{filename}")
                if downloaded_urls:
                    response["download_urls"] = downloaded_urls
        except Exception as e:
            logger.warning("File download post-processing failed: %s", e)
            # Never break the main agent response over file download

        # Extract answer only after successful invoke
        answer = response["messages"][-1].content

        print("\n===== AGENT RESPONSE DEBUG =====")
        print(f"Model: {response['messages'][-1].response_metadata.get('model_name', 'unknown')}")
        print(f"Total messages: {len(response['messages'])}")
        print(f"Answer preview: {answer[:200]}...")
        print("================================\n")

        #  SAVE AI RESPONSE INTO DB
        add_ai_response(
            document_id=request.document_id,
            query=request.query,
            response=answer
        )
        # SAVE RESEARCH MEMORY

        try:
            memory_entry = create_memory_entry(
                query=request.query,
                answer=answer
            )

            if memory_entry:
                save_memory_entry(memory_entry)
                print("Memory saved successfully.") 

        except Exception as memory_error:
            print(
                f"Memory save failed: {memory_error}"
            )

        # Return response
        result = {
            "answer": answer
        }
        if "download_urls" in response:
            result["download_urls"] = response["download_urls"]
        return result
    
    except Exception as e:
        # Handle any agent errors (GraphRecursionError, LLM errors, etc.)
        error_message = f"Agent failed: {str(e)}"
        print(f"\n===== AGENT ERROR =====")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("=====================\n")
        
        return {
            "answer": error_message
        }


@router.post("/field-search")
async def field_search(request: FieldSearchRequest):
    fields = [field.strip() for field in request.fields if field.strip()]

    if not fields:
        return {
            "answer": "Add at least one field or search key to extract from the document."
        }

    field_search_thread_id = f"field-search:{request.document_id or uuid4()}"
    agent = get_deep_rag_agent(request.document_id, thread_id=field_search_thread_id)
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

    # Run agent with error handling
    try:
        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },

            config={
                # Recursion limit for multi-step planning with specialized tools.
                "recursion_limit": 25,
                "configurable": {
                    "thread_id": field_search_thread_id
                }
            }
        )

        # Extract answer only after successful invoke
        answer = response["messages"][-1].content

        print("\n===== AGENT RESPONSE DEBUG =====")
        print(f"Model: {response['messages'][-1].response_metadata.get('model_name', 'unknown')}")
        print(f"Total messages: {len(response['messages'])}")
        print(f"Answer preview: {answer[:200]}...")
        print("================================\n")

        add_ai_response(
            document_id=request.document_id,
            query=f"Field search: {', '.join(fields)}",
            response=answer
        )

        return {
            "answer": answer
        }
    
    except Exception as e:
        # Handle any agent errors (GraphRecursionError, LLM errors, etc.)
        error_message = f"Agent failed: {str(e)}"
        print(f"\n===== AGENT ERROR =====")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("=====================\n")
        
        return {
            "answer": error_message
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
