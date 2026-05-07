from langchain_openai import ChatOpenAI
from app.services.retrieval_service import search_documents
import json
import os
import re

llm = ChatOpenAI(model="gpt-5.4-nano")

DEFAULT_METADATA_FIELDS = ["name", "location", "date"]


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


def extract_default_metadata(extracted_text: str, file_name: str):
    context = extracted_text[:8000]

    prompt = f"""
You extract basic document metadata.

Return ONLY valid JSON with these exact keys:
{{
  "name": string or null,
  "location": string or null,
  "date": string or null
}}

Rules:
- "name" means the document name or title. Prefer a title inside the document. If no title exists, use the uploaded file name without extension only if it is meaningful.
- "location" means a location mentioned by the document, only if applicable.
- "date" means the main document date, only if present.
- Use null when the value is not found.
- Do not include markdown, explanation, evidence, or extra keys.

Uploaded file name:
{file_name}

Document text:
{context}
"""

    fallback = {
        "name": os.path.splitext(file_name)[0] or None,
        "location": None,
        "date": None,
    }

    try:
        response = llm.invoke(prompt)
        raw_content = response.content.strip()
        json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        parsed = json.loads(json_match.group(0) if json_match else raw_content)
    except Exception:
        return fallback

    return {
        field: parsed.get(field) if parsed.get(field) not in ("", "Not found", "null") else None
        for field in DEFAULT_METADATA_FIELDS
    }
