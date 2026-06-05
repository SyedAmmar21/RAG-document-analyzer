from email.mime import text
from multiprocessing import context
from unittest import result
from langchain.tools import tool
from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import re
from collections import defaultdict

from app.services.retrieval_service import search_documents


# ========================================
# HELPER FUNCTIONS
# ========================================

def clean_chunk_text(text: str) -> str:
    """
    Remove boilerplate content from chunks.
    
    Filters out common navigation and footer content:
    - Contact Us, Privacy Policy, FAQ, Subscribe
    - Newsletter signup forms
    - Terms of Service, Cookie Policy
    - Common footer/navigation patterns
    
    Args:
        text: Raw chunk text
        
    Returns:
        Cleaned chunk text with boilerplate removed
    """
    boilerplate_patterns = [
        r"(?i)contact\s+us.*?(?=\n|$)",
        r"(?i)privacy\s+policy.*?(?=\n|$)",
        r"(?i)terms\s+of\s+service.*?(?=\n|$)",
        r"(?i)cookie\s+polic(?:y|ies).*?(?=\n|$)",
        r"(?i)faq.*?(?=\n|$)",
        r"(?i)subscribe.*?(?=\n|$)",
        r"(?i)newsletter.*?(?=\n|$)",
        r"(?i)unsubscribe.*?(?=\n|$)",
        r"(?i)© \d{4}.*?(?=\n|$)",
        r"(?i)all rights reserved.*?(?=\n|$)",
        r"(?i)powered by.*?(?=\n|$)",
    ]
    
    cleaned = text
    for pattern in boilerplate_patterns:
        cleaned = re.sub(pattern, "", cleaned)
    
    # Remove multiple consecutive newlines
    cleaned = re.sub(r"\n\n+", "\n\n", cleaned)
    
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned


def normalize_document_name(doc_name: str) -> str:
    """
    Normalize document names to detect variants (e.g., report.pdf vs report.txt).
    
    Args:
        doc_name: Original document name
        
    Returns:
        Normalized name without extension
    """
    # Remove file extension
    return re.sub(r'\.\w+$', '', doc_name).lower()


def get_document_group_key(doc_name: str) -> str:
    """
    Get grouping key for document variants.
    
    Treats report.pdf and report.txt as the same document.
    
    Args:
        doc_name: Document name
        
    Returns:
        Normalized document key
    """
    return normalize_document_name(doc_name)


# tools
def create_tools(llm, document_id=None, document_ids=None):

    # tool 1
    @tool
    def search_documents_tool(query: str):
        """
        Search relevant document chunks from Elasticsearch based on the user's query.
        
        Returns clean evidence with source attribution for factual questions and quick answers.
        
        Use this tool for:
        - Factual questions
        - Quick answers
        - Document summaries
        - Direct information lookup
        """
        results = search_documents(query, document_id=document_id, document_ids=document_ids, top_k=8)
        
        # ========================================
        # LOGGING
        # ========================================
        unique_docs = set(r["document_name"] for r in results)
        
        print(f"\n===== SEARCH DOCUMENTS =====")
        print(f"Query: {query}")
        print(f"Results Found: {len(results)}")
        print(f"Unique Documents: {len(unique_docs)}")
        print("=============================\n")
        
        if not results:
            return "No relevant information found."

        # ========================================
        # BUILD CLEAN EVIDENCE CONTEXT
        # ========================================
        
        context = "RETRIEVED EVIDENCE\n\n"
        
        seen_chunks = set()
        
        for result in results:
            document_name = result["document_name"]
            text = result["text"].strip()
            
            # Skip duplicate chunks
            text_hash = hash(text)
            if text_hash in seen_chunks:
                continue
            seen_chunks.add(text_hash)
            
            # Clean boilerplate content
            cleaned_text = clean_chunk_text(text)
            
            # Truncate oversized chunks
            truncated_text = cleaned_text[:1000]
            
            context += f"""[Source: {document_name}]
{truncated_text}

---

"""

        return context


    # 🔹 tool 2
    @tool
    def summarize_document_tool(query: str):
        """
        Summarize the document based on relevant content.
        Use this tool when the user asks for a summary or overview of the document.
        """

        # Get more chunks for better summary
        results = search_documents(query, document_id=document_id, document_ids=document_ids, top_k=8)
        
        # ========================================
        # LOGGING
        # ========================================
        unique_docs = set(r["document_name"] for r in results)
        
        print(f"\n===== SUMMARIZE DOCUMENT =====")
        print(f"Query: {query}")
        print(f"Results Found: {len(results)}")
        print(f"Unique Documents: {len(unique_docs)}")
        print("===============================\n")
        
        # Clean chunks before processing
        cleaned_chunks = []
        for result in results:
            text = result["text"].strip()
            cleaned_text = clean_chunk_text(text)
            cleaned_chunks.append(cleaned_text)
        
        context = "\n\n".join(cleaned_chunks)

        prompt = f"""
You are an expert at summarizing documents.

Provide a clear and concise summary of the following content.
Focus on the most important points and key takeaways.

Content:
{context}

User Request:
{query}
"""

        response = llm.invoke(prompt)

        return response.content
    
    # 🔹 tool 3
    @tool
    def deep_research_tool(query: str, top_k: int = 40):
        """
        Perform comprehensive multi-document analysis with advanced deduplication.

        Use this tool when the user asks for:
        - comparisons
        - contradictions
        - trends
        - comprehensive reviews
        - strategic analysis
        - deep research
        - executive summaries
        
        Args:
            query: Research question
            top_k: Number of chunks to retrieve (default 40 for comprehensive analysis)
        """

        print(f"\n===== DEEP RESEARCH =====")
        print(f"Query: {query}")
        print(f"Top K: {top_k}")

        # Retrieve comprehensive evidence
        results = search_documents(
            query,
            document_id=document_id,
            document_ids=document_ids,
            top_k=top_k
        )

        print(f"Results Found: {len(results)}")

        if not results:
            return "No relevant information found."

        # ========================================
        # DEDUPLICATION AND GROUPING
        # ========================================
        
        # Group by normalized document name to handle variants (pdf, txt, etc.)
        document_groups = defaultdict(list)
        seen_chunks = set()
        
        for result in results:
            doc_name = result["document_name"]
            text = result["text"].strip()
            
            # Skip duplicate chunks (exact text match)
            text_hash = hash(text)
            if text_hash in seen_chunks:
                continue
            seen_chunks.add(text_hash)
            
            # Group by normalized document key (handles report.pdf vs report.txt)
            group_key = get_document_group_key(doc_name)
            document_groups[group_key].append({
                "original_name": doc_name,
                "text": text,
                "score": result.get("score", 0)
            })
        
        # Keep only top 5 chunks per document (by score)
        for group_key in document_groups:
            chunks = document_groups[group_key]
            # Sort by score descending
            chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
            # Keep top 5
            document_groups[group_key] = chunks[:5]
        
        # ========================================
        # STRUCTURED CONTEXT BUILDING
        # ========================================
        
        context = """
DEEP RESEARCH ANALYSIS

Structured evidence retrieved across multiple documents.

Instructions for analysis:
- Compare viewpoints across all documents
- Identify areas of agreement and disagreement
- Identify recurring themes and patterns
- Highlight contradictions
- Discuss implications and strategic risks
- Produce evidence-backed conclusions
- Estimate confidence in findings

==========================================
"""

        # Build context with organized document sections
        for group_key, chunks in sorted(document_groups.items()):
            # Use the first (original) document name for display
            doc_display_name = chunks[0]["original_name"]
            
            context += f"""
DOCUMENT: {doc_display_name}
==========================================

Key Evidence:

"""
            
            for i, chunk_data in enumerate(chunks, 1):
                chunk_text = chunk_data["text"]
                # Clean boilerplate
                cleaned_text = clean_chunk_text(chunk_text)
                # Truncate if too long
                truncated_text = cleaned_text[:1500]
                
                context += f"""Chunk {i}:
{truncated_text}

"""
            
            context += "\n"
        
        # ========================================
        # LOGGING
        # ========================================
        
        total_chunks_used = sum(len(chunks) for chunks in document_groups.values())
        
        print(f"Unique Documents: {len(document_groups)}")
        print(f"Total Chunks Kept: {total_chunks_used}")
        
        for group_key, chunks in sorted(document_groups.items()):
            doc_name = chunks[0]["original_name"]
            chunks_count = len(chunks)
            print(f"  {doc_name} → {chunks_count} chunk(s)")
        
        print("============================\n")

        return context

    return [search_documents_tool, summarize_document_tool, deep_research_tool]





# agent
def get_rag_agent(document_id: str | None = None, document_ids: list[str] | None = None):
    llm = ChatOpenAI(model="gpt-5.4-nano")

    tools = create_tools(llm=llm, document_id=document_id, document_ids=document_ids)

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
You are an intelligent document search and retrieval assistant.

Your job:
- Understand the user's question carefully
- Use appropriate tools to retrieve relevant information
- Provide clear, evidence-based answers

Tool usage:
- search_documents_tool: For factual questions, quick answers, information lookups
- summarize_document_tool: For document summaries and overviews
- For analysis or comparison questions, consider using the deep RAG agent instead

Answer quality:
- Always base your answer ONLY on retrieved document content
- Cite your sources explicitly
- Do NOT hallucinate, speculate, or go beyond retrieved evidence
- When evidence is limited, acknowledge this explicitly

If no relevant information is found, clearly say so.
"""
    )

    return agent

def get_deep_rag_agent(
    document_id: str | None = None,
    document_ids: list[str] | None = None
):
    llm = ChatOpenAI(model="gpt-5.4-nano")

    tools = create_tools(
        llm=llm,
        document_id=document_id,
        document_ids=document_ids
    )

    agent = create_deep_agent(
        model=llm,
        tools=tools,
        skills=[
            "app/skills/retrieval_strategy.md",
            "app/skills/analytical_review.md",
            "app/skills/comparative_analysis.md"
        ],
        system_prompt="""
You are an expert document analyst and research agent.

Your capabilities:
- Deep research tool: For comprehensive multi-document analysis, comparison, and synthesis
- Search tool: For factual lookups and quick answers
- Summarization tool: For document overviews

Your responsibilities:

1. TOOL SELECTION
   - Use retrieval_strategy.md skill to choose the right tool for each query
   - Deep research for analysis, comparison, trends, risks
   - Search for factual questions and quick answers
   - Be strategic about tool combinations

2. EVIDENCE-BASED REASONING
   - Base ALL conclusions ONLY on retrieved evidence
   - Cite sources explicitly
   - Do NOT hallucinate or speculate beyond evidence
   - Acknowledge uncertainty when evidence is limited

3. CROSS-DOCUMENT SYNTHESIS
   - When analyzing multiple documents, actively compare viewpoints
   - Identify agreements, disagreements, and complementary information
   - Synthesize across sources rather than summarizing each individually
   - Use analytical_review.md skill for structured analysis

4. QUALITY STANDARDS
   - Provide evidence-backed conclusions
   - Estimate confidence in findings
   - Distinguish between direct evidence and inference
   - Explicitly report uncertainty and gaps
   - Avoid isolated per-document summaries
   - Prevent contradictions within your reasoning

5. STRUCTURED OUTPUT
   - For complex questions, use structured formats (executive summary, key findings, etc.)
   - Organize information logically
   - Make reasoning transparent
   - Provide clear attribution for all claims

When no relevant information is found, clearly say so.
""",
        debug=True
        
    )

    return agent