from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_agent_service import get_rag_agent
from app.services.document_service import add_ai_response

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

    folder_ids: list[int] = []

    document_ids: list[str] = []

class FieldSearchRequest(BaseModel):
    fields: list[str]
    document_id: str

# Endpoint
@router.post("/query")
async def query_agent(request: QueryRequest):
    # Create agent for specific document
    agent = get_rag_agent(request.document_id)

    # Run agent
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": request.query}
        ]
    })

    # Extract answer
    answer = response["messages"][-1].content

    print("SAVING RESPONSE:", request.document_id)

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
