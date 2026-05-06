from langchain_openai import ChatOpenAI
from app.services.retrieval_service import search_documents

llm = ChatOpenAI(model="gpt-5.4-nano")


def extract_fields(document_id: str, fields: list[str]):
    results = search_documents(
        query="Extract requested information from document",
        document_id=document_id,
        top_k=8
    )

    context = "\n\n".join(results)

    fields_str = ", ".join(fields)

    prompt = f"""
You are an AI that extracts specific information from documents.

Extract ONLY the following fields:
{fields_str}

Return results in this format:
Field: value

If not found, return:
Field: Not found

Do NOT return JSON or markdown.

Document:
{context}
"""

    response = llm.invoke(prompt)
    return response.content
