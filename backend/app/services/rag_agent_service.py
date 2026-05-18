from email.mime import text
from multiprocessing import context
from unittest import result

from langchain.tools import tool
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.services.retrieval_service import search_documents


# tools
def create_tools(llm, document_id=None, document_ids=None):

    # tool 1
    @tool
    def search_documents_tool(query: str):
        """
        Search relevant document chunks from Elasticsearch based on the user's query.
        Use this tool for general questions about the document.
        """
        results = search_documents(query, document_id=document_id, document_ids=document_ids, top_k=8)
        if not results:
            return "No relevant information found."

        context = f"""
                RETRIEVAL CONTEXT

                You are receiving document chunks that were intentionally retrieved
                from the user's currently selected retrieval scope.

                IMPORTANT:
                - Treat the retrieved chunks as the authoritative representation
                  of the selected documents/folders.
                - Do NOT say you lack access to the folders/documents.
                - Do NOT ask the user to provide folder names again.
                - Base your reasoning ONLY on the retrieved evidence below.
                - Synthesize themes, patterns, comparisons, and insights confidently
                  from the provided context.
                - When referencing information, naturally mention the source document name when relevant.
                - If multiple documents contribute to a conclusion, mention the contributing documents.
                - Use grounded attribution such as:
                      "According to [document name]..."
                      "The [document name] states..."
                      "Multiple retrieved documents suggest..."  

                RETRIEVAL MODE:
                {"Multiple Documents" if document_ids else "Single Document" if document_id else "Global Search"}

                ====================
                """

        source_documents = set()

        for result in results:
           source_documents.add(result["document_name"])

        sources_text = "\n".join(
             f"- {doc}"
             for doc in sorted(source_documents)
        )

        context += f"""

            SOURCE DOCUMENTS INCLUDED:
            {sources_text}

            ====================

           """

        seen_chunks = set()

        for result in results:
            document_name = result["document_name"]
            text = result["text"].strip()

            # skip duplicate chunks
            if text in seen_chunks:
                continue

            seen_chunks.add(text)

            # truncate oversized chunks
            cleaned_text = text[:2000]

            context += f"""
        DOCUMENT: {document_name}

        {cleaned_text}

        --------------------
        """

        return context


    # 🔹 tool 2
    @tool
    def summarize_document_tool(query: str):
        """
        Summarize the document based on relevant content.
        Use this tool when the user asks for a summary or overview of the document.
        """

        # get more chunks for better summary
        results = search_documents(query, document_id=document_id, document_ids=document_ids, top_k=8)
        context = "\n\n".join([result["text"] for result in results])

        prompt = f"""
You are an expert at summarizing documents.

Provide a clear and concise summary of the following content.
Focus on the most important points.

Document:
{context}

User Request:
{query}
"""

        response = llm.invoke(prompt)

        return response.content


    return [search_documents_tool, summarize_document_tool]





# agent
def get_rag_agent(document_id: str | None = None, document_ids: list[str] | None = None):
    llm = ChatOpenAI(model="gpt-5.4-nano")

    tools = create_tools(llm=llm, document_id=document_id, document_ids=document_ids)

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
You are an intelligent document assistant.

Your job and rules:
- Understand the user's question carefully
- Use search_documents_tool for general questions and explanations
- Use summarize_document_tool when the user asks for a summary, overview of the document or explination of whole document

- Always base your answer ONLY on retrieved document content
- Do NOT hallucinate or guess

If no relevant information is found, clearly say so.
"""
    )

    return agent
