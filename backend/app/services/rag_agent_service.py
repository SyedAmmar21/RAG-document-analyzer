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
        results = search_documents(query, document_id=document_id, document_ids=document_ids, top_k=4)
        if not results:
            return "No relevant information found."

        context = ""

        for result in results:
            document_name = result["document_name"]
            text = result["text"]

            context += f"""
        DOCUMENT: {document_name}

        {text}

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
