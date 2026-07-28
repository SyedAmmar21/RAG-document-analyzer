import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from app.core.paths import OUTPUT_DIR
from app.services.rag_agent_service import get_deep_rag_agent
from app.services.presentation_workflow import is_presentation_request
from app.services.document_service import add_ai_response
from app.services.domain_service import get_documents_by_domain

from app.services.memory_service import (
    create_memory_entry,
    save_memory_entry
)

from app.services.sandbox.session_store import (
    consume_output_files,
    get_current_document,
    get_existing_backend,
    set_current_document,
    WorkingDocument,
)

from app.services.redis_store_service import search_research_memories

router = APIRouter()
logger = logging.getLogger(__name__)


def _download_sandbox_file_bytes(sandbox_backend, sandbox_path: str) -> bytes | None:
    download_file_bytes = getattr(sandbox_backend, "download_file_bytes", None)
    if callable(download_file_bytes):
        return download_file_bytes(sandbox_path)

    raise RuntimeError(
        f"Sandbox backend does not implement download_file_bytes(): {type(sandbox_backend)!r}"
    )


def _is_download_request(user_query: str) -> bool:
    lowered = user_query.lower()
    return any(
        phrase in lowered
        for phrase in (
            "download it",
            "download the file",
            "download the document",
            "download the presentation",
            "download the report",
            "download the spreadsheet",
            "download",
        )
    )


def _existing_download_urls_for_thread(thread_id: str) -> list[str]:
    current_document = get_current_document(thread_id)
    if current_document is None:
        return []

    output_path = OUTPUT_DIR / current_document.filename
    if not output_path.exists() or not output_path.is_file():
        return []

    return [f"/download/{current_document.filename}"]


def _append_download_links(answer: str, download_urls: list[str]) -> str:
    if not download_urls:
        return answer

    lines = [answer.rstrip(), "", "Generated file download:"]
    for url in download_urls:
        lines.append(f"- {url}")

    return "\n".join(lines).strip()


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
    presentation_requested = is_presentation_request(request.query)

    # GLOBAL mode
    if request.scope_type == "global":
        agent = get_deep_rag_agent(
            thread_id=request.thread_id,
            presentation_requested=presentation_requested,
        )

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
            thread_id=request.thread_id,
            presentation_requested=presentation_requested,
        )

    # DOCUMENT mode
    elif request.scope_type == "documents":
        agent = get_deep_rag_agent(
            document_ids=request.document_ids,
            thread_id=request.thread_id,
            presentation_requested=presentation_requested,
        )

    # FALLBACK single-document compatibility
    else:
        agent = get_deep_rag_agent(
            document_id=request.document_id,
            thread_id=request.thread_id,
            presentation_requested=presentation_requested,
        )
    # ========================================
    # PRELOAD REDIS MEMORIES
    # ========================================

    memory_keywords = [
        "remember",
        "memory",
        "previous",
        "previously",
        "before",
        "earlier",
        "last time",
        "historical",
        "prior",
        "conclusion",
        "concluded",
        "finding",
        "findings",
        "research",
    ]

    user_message = request.query

    if any(keyword in user_message.lower() for keyword in memory_keywords):

        memories = search_research_memories(
            query=user_message,
            limit=5,
        )

        if memories:

            print(f"Loaded {len(memories)} Redis memories.")

            sections = []

            for item in memories:
                value = item.value

                sections.append(
                    f"""
Question:
{value.get("query")}

Summary:
{value.get("summary")}
"""
                )

            memory_context = (
                "Previous research memories:\n\n"
                + "\n\n----------------------\n\n".join(sections)
            )

            user_message = f"""
{memory_context}

----------------------------------------

Current user question:

{request.query}
"""
    # Run agent with error handling
    try:
        response = await asyncio.to_thread(
            agent.invoke,
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            },
            config={
                # Recursion limit for multi-step planning with specialized tools.
                # Each tool call + reasoning step counts as 1 recursion iteration.
                "recursion_limit": 75,
                "configurable": {
                    "thread_id": request.thread_id
                }
            }
        )

        # Post-invoke: download any files the agent generated in sandbox
        try:
            filenames = consume_output_files(request.thread_id)
            sandbox_backend = get_existing_backend(request.thread_id)

            downloaded_urls = []

            if sandbox_backend is not None and filenames:
                for filename in filenames:
                    content = await asyncio.to_thread(
                        _download_sandbox_file_bytes,
                        sandbox_backend,
                        f"/workspace/output/{filename}",
                    )
                    if content is not None:
                        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                        out_path = OUTPUT_DIR / filename
                        out_path.write_bytes(content)
                        downloaded_urls.append(f"/download/{filename}")

                        extension = Path(filename).suffix.lower()

                        if extension in {".pptx", ".docx", ".xlsx"}:
                            set_current_document(
                                request.thread_id,
                                WorkingDocument(
                                    filename=filename,
                                    path=f"/workspace/output/{filename}",
                                    file_type=extension[1:],  # pptx/docx/xlsx
                                ),
                            )
                        
                        # Keep generated files in the sandbox so they can be edited
                        # sandbox_backend.execute(f"rm /workspace/output/{filename}")
            if not downloaded_urls and _is_download_request(request.query):
                downloaded_urls = _existing_download_urls_for_thread(request.thread_id)

            if downloaded_urls:
                response["download_urls"] = downloaded_urls
        except Exception as e:
            logger.warning("File download post-processing failed: %s", e)
            # Never break the main agent response over file download

        # Extract answer only after successful invoke
        answer = response["messages"][-1].content
        if "download_urls" in response:
            answer = _append_download_links(answer, response["download_urls"])

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
                save_memory_entry(query=request.query,memory_entry=memory_entry,)
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



