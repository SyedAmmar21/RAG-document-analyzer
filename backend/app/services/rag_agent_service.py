from multiprocessing import context
from langchain.tools import tool
from deepagents import create_deep_agent
from langchain_aws import ChatBedrockConverse
import json
import re
import os
from collections import defaultdict

from app.services.retrieval_service import search_documents
from app.services.memory_retrieval_service import get_memory_content
from langchain_aws.middleware.prompt_caching import BedrockPromptCachingMiddleware
from langgraph.checkpoint.memory import MemorySaver
from deepagents.backends import (
    FilesystemBackend,
    CompositeBackend,
    StoreBackend,
)

from langgraph.store.redis import RedisStore
from redis import Redis

# ========================================
# HELPER FUNCTIONS
# ========================================
memory_checkpointer = MemorySaver()

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


# SHARED RETRIEVAL HELPER FUNCTION


def build_research_context(
    query: str,
    document_id: str | None = None,
    document_ids: list[str] | None = None,
    top_k: int = 40
) -> dict:
    """
    Retrieve and structure evidence for analysis tools.
    
    This shared helper performs comprehensive retrieval, deduplication, and 
    document grouping. All specialized analysis tools (compare, trends, risks)
    should use this to retrieve evidence, enabling the Deep Agent to:
    - Analyze the same evidence from multiple perspectives
    - Make informed decisions about which tools to use
    - Plan multi-step analyses more effectively
    
    Args:
        query: Research question or retrieval prompt
        document_id: Single document scope (optional)
        document_ids: Multiple document scope (optional)
        top_k: Number of chunks to retrieve (default 40 for comprehensive analysis)
    
    Returns:
        dict with keys:
            - 'query': The original query
            - 'raw_results': Original Elasticsearch results (count, sources)
            - 'document_groups': Organized evidence by document
            - 'formatted_context': Ready-to-use evidence string
            - 'metadata': Statistics (unique_documents, total_chunks, etc.)
    """
    
    # Retrieve comprehensive evidence from Elasticsearch
    results = search_documents(
        query,
        document_id=document_id,
        document_ids=document_ids,
        top_k=top_k
    )
    
    if not results:
        return {
            'query': query,
            'raw_results': [],
            'document_groups': {},
            'formatted_context': 'No relevant information found.',
            'metadata': {
                'unique_documents': 0,
                'total_chunks': 0,
                'retrieved_results': 0
            }
        }

    # DEDUPLICATION AND GROUPING
 
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
        chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        document_groups[group_key] = chunks[:5]
    
    # ========================================
    # FORMAT CONTEXT FOR ANALYSIS
    # ========================================
    formatted_context = """
RETRIEVED EVIDENCE FOR ANALYSIS

Structured evidence across multiple documents.
Use this evidence to perform your specialized analysis task.

==========================================
"""
    
    for group_key, chunks in sorted(document_groups.items()):
        doc_display_name = chunks[0]["original_name"]
        
        formatted_context += f"""
DOCUMENT: {doc_display_name}
==========================================

"""
        
        for i, chunk_data in enumerate(chunks, 1):
            chunk_text = chunk_data["text"]
            cleaned_text = clean_chunk_text(chunk_text)
            truncated_text = cleaned_text[:1500]
            
            formatted_context += f"""[Chunk {i}]
{truncated_text}

"""
        
        formatted_context += "\n"
    
    # ========================================
    # COMPUTE METADATA
    # ========================================
    total_chunks_used = sum(len(chunks) for chunks in document_groups.values())
    
    return {
        'query': query,
        'raw_results': results,
        'document_groups': document_groups,
        'formatted_context': formatted_context,
        'metadata': {
            'unique_documents': len(document_groups),
            'total_chunks': total_chunks_used,
            'retrieved_results': len(results),
            'documents': {
                chunks[0]["original_name"]: len(chunks) 
                for chunks in document_groups.values()
            }
        }
    }



def create_tools(llm, document_id=None, document_ids=None, thread_id="default"):
    def _get_output_file_state(backend) -> dict[str, str]:
        state_command = (
            "find /workspace/output -maxdepth 1 -type f "
            "-printf '%f\\t%TY-%Tm-%Td %TH:%TM:%TS\\n' 2>/dev/null || true"
        )
        result = backend.execute(state_command)
        file_state = {}

        for line in result.output.splitlines():
            if not line.strip() or "\t" not in line:
                continue
            filename, modified_at = line.split("\t", 1)
            file_state[filename.strip()] = modified_at.strip()

        return file_state

    # TOOL 1: SEARCH DOCUMENTS

    @tool
    def search_documents_tool(query: str):
        """
        Search relevant document chunks from Elasticsearch based on the user's query.
        
        Returns clean evidence with source attribution for factual questions and quick answers.
        
        Use for:
        - Factual questions and lookups
        - Quick answers and direct evidence
        - When you need specific information before deeper analysis
        - Document summaries and overview questions
        """
        results = search_documents(query, document_id=document_id, document_ids=document_ids, top_k=8)
        

        # LOGGING

        unique_docs = set(r["document_name"] for r in results)
        
        print(f"\n===== SEARCH DOCUMENTS TOOL =====")
        print(f"Query: {query}")
        print(f"Results Found: {len(results)}")
        print(f"Unique Documents: {len(unique_docs)}")
        print("==================================\n")
        
        if not results:
            return "No relevant information found."


        # BUILD CLEAN EVIDENCE CONTEXT

        
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



    # TOOL 2: SUMMARIZE DOCUMENT
    
    @tool
    def summarize_document_tool(query: str):
        """
        Summarize the document based on relevant content.
        
        Use when:
        - The user asks for a summary or overview
        - You need to understand the document's main themes before analysis
        - Creating an executive overview of document(s)
        - Condensing content for strategic decision-making
        """

        # Get more chunks for better summary
        results = search_documents(query, document_id=document_id, document_ids=document_ids, top_k=8)
        
 
        # LOGGING

        unique_docs = set(r["document_name"] for r in results)
        
        print(f"\n===== SUMMARIZE DOCUMENT TOOL =====")
        print(f"Query: {query}")
        print(f"Results Found: {len(results)}")
        print(f"Unique Documents: {len(unique_docs)}")
        print("===================================\n")
        
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
    

    # TOOL 3: COMPARE DOCUMENTS
    
    @tool
    def compare_documents_tool(query: str):
        """
        Compare viewpoints and perspectives across retrieved documents.
        
        Identifies agreements, disagreements, complementary views, and conflicting claims.
        
        Use when:
        - Comparing different documents' viewpoints
        - Analyzing conflicting opinions or forecasts
        - Understanding different perspectives on the same topic
        - Identifying consensus vs. dissent across sources
        - Evaluating different approaches or strategies
        """
        
        print(f"\n===== COMPARE DOCUMENTS TOOL =====")
        print(f"Query: {query}")
        
        # Use shared helper to retrieve evidence
        context_data = build_research_context(
            query,
            document_id=document_id,
            document_ids=document_ids,
            top_k=30
        )
        
        print(f"Unique Documents: {context_data['metadata']['unique_documents']}")
        print(f"Total Chunks: {context_data['metadata']['total_chunks']}")
        print("==================================\n")
        
        if context_data['metadata']['unique_documents'] == 0:
            return "No relevant information found for comparison."
        
        # Use LLM to perform comparative analysis
        prompt = f"""
You are an expert at comparing viewpoints and perspectives across documents.

Analyze the following evidence and provide a structured comparison:

{context_data['formatted_context']}

ANALYSIS TASK:
{query}

Provide your analysis with these sections:
1. AREAS OF AGREEMENT: Where do documents align?
2. AREAS OF DISAGREEMENT: Where do they conflict?
3. UNIQUE PERSPECTIVES: What does each document contribute uniquely?
4. CONFIDENCE ASSESSMENT: How confident are you in these comparisons?
5. IMPLICATIONS: What are the strategic implications of these differences?

Always cite sources explicitly for each claim.
"""
        
        response = llm.invoke(prompt)
        return response.content
    

    # TOOL 4: IDENTIFY TRENDS
    
    @tool
    def identify_trends_tool(query: str):
        """
        Extract recurring themes, trends, patterns, and emerging signals from documents.
        
        Identifies recurring concepts, trends over time, emerging signals, and patterns.
        
        Use when:
        - Looking for trends, patterns, or themes
        - Identifying recurring concepts across documents
        - Spotting emerging signals or weak signals
        - Understanding theme evolution
        - Analyzing industry patterns or market trends
        - Finding cause-and-effect patterns
        """
        
        print(f"\n===== IDENTIFY TRENDS TOOL =====")
        print(f"Query: {query}")
        
        # Use shared helper to retrieve evidence
        context_data = build_research_context(
            query,
            document_id=document_id,
            document_ids=document_ids,
            top_k=30
        )
        
        print(f"Unique Documents: {context_data['metadata']['unique_documents']}")
        print(f"Total Chunks: {context_data['metadata']['total_chunks']}")
        print("================================\n")
        
        if context_data['metadata']['unique_documents'] == 0:
            return "No relevant information found for trend analysis."
        
        # Use LLM to identify patterns and trends
        prompt = f"""
You are an expert at identifying trends, patterns, and recurring themes.

Analyze the following evidence and extract trends and patterns:

{context_data['formatted_context']}

ANALYSIS TASK:
{query}

Provide your analysis with these sections:
1. RECURRING THEMES: What concepts appear repeatedly?
2. TRENDS IDENTIFIED: What patterns or trends emerge?
3. EMERGING SIGNALS: What weak signals or early indicators exist?
4. TEMPORAL PATTERNS: Is there a timeline or evolution?
5. CROSS-DOCUMENT PATTERNS: What connects these documents?
6. CONFIDENCE LEVELS: How strong is the evidence for each pattern?

Always cite specific sources and evidence for each pattern identified.
"""
        
        response = llm.invoke(prompt)
        return response.content
    

    # TOOL 5: RISK ANALYSIS
    
    @tool
    def risk_analysis_tool(query: str):
        """
        Identify risks, uncertainties, contradictions, and confidence signals.
        
        Analyzes potential weaknesses, contradictions, uncertainty levels, and confidence.
        
        Use when:
        - Assessing risks and uncertainties
        - Identifying contradictions in evidence
        - Evaluating confidence levels
        - Finding potential weaknesses or gaps
        - Analyzing threats and concerns
        - Identifying areas of uncertainty or debate
        """
        
        print(f"\n===== RISK ANALYSIS TOOL =====")
        print(f"Query: {query}")
        
        # Use shared helper to retrieve evidence
        context_data = build_research_context(
            query,
            document_id=document_id,
            document_ids=document_ids,
            top_k=30
        )
        
        print(f"Unique Documents: {context_data['metadata']['unique_documents']}")
        print(f"Total Chunks: {context_data['metadata']['total_chunks']}")
        print("==============================\n")
        
        if context_data['metadata']['unique_documents'] == 0:
            return "No relevant information found for risk analysis."
        
        # Use LLM to perform risk analysis
        prompt = f"""
You are an expert at identifying risks, uncertainties, and contradictions.

Analyze the following evidence and assess risks and uncertainties:

{context_data['formatted_context']}

ANALYSIS TASK:
{query}

Provide your analysis with these sections:
1. IDENTIFIED RISKS: What risks or threats are present?
2. CONTRADICTIONS: Where does evidence contradict itself?
3. UNCERTAINTY AREAS: Where is the evidence weak or unclear?
4. CONFIDENCE SIGNALS: What increases or decreases confidence?
5. POTENTIAL WEAKNESSES: What gaps or vulnerabilities exist?
6. CONFIDENCE ASSESSMENT: Overall confidence level and why?

Always cite sources and provide evidence for each risk or contradiction identified.
"""
        
        response = llm.invoke(prompt)
        return response.content

    # TOOL 6: DEEP RESEARCH (SYNTHESIS)
    
    @tool
    def deep_research_tool(query: str, top_k: int = 40):
        """
        Synthesize evidence into executive-level conclusions and strategic insights.
        
        Performs comprehensive synthesis focusing on implications, opportunities,
        strategic insights, and actionable conclusions rather than retrieving
        and repeating all evidence.
        
        Use when:
        - You need executive-level synthesis and strategic recommendations
        - Synthesizing findings from multiple specialized analyses
        - Generating investment analysis or strategic reviews
        - Creating comprehensive conclusions after investigation
        - Generating forward-looking strategic insights
        
        Note: This tool specializes in SYNTHESIS, not retrieval. Use comparison,
        trends, and risk tools first to gather specialized analyses.
        
        Args:
            query: Research question or synthesis prompt
            top_k: Number of chunks to retrieve for context (default 40)
        """

        print(f"\n===== DEEP RESEARCH TOOL (SYNTHESIS) =====")
        print(f"Query: {query}")
        print(f"Top K: {top_k}")
        
        # Use shared helper to retrieve evidence
        context_data = build_research_context(
            query,
            document_id=document_id,
            document_ids=document_ids,
            top_k=top_k
        )
        
        print(f"Unique Documents: {context_data['metadata']['unique_documents']}")
        print(f"Total Chunks: {context_data['metadata']['total_chunks']}")
        print("=========================================\n")
        
        if context_data['metadata']['unique_documents'] == 0:
            return "No relevant information found for synthesis."
        
        # Use LLM to synthesize into strategic conclusions
        prompt = f"""
You are an expert research synthesizer creating executive-level conclusions.

Based on the following evidence, provide strategic synthesis and conclusions:

{context_data['formatted_context']}

RESEARCH QUESTION:
{query}

Provide your synthesis with these sections:
1. EXECUTIVE SUMMARY: High-level findings and conclusions
2. KEY INSIGHTS: What are the most important takeaways?
3. STRATEGIC IMPLICATIONS: What do these findings mean strategically?
4. OPPORTUNITIES: What opportunities emerge from this evidence?
5. RECOMMENDATIONS: What actions should be taken based on findings?
6. CONCLUSION: Your final assessment and outlook

Focus on:
- Synthesizing across sources rather than repeating each document
- Drawing conclusions and implications beyond what's explicitly stated
- Identifying strategic opportunities and risks
- Providing actionable recommendations
- Always citing sources for factual claims
- Being explicit about confidence levels and limitations

Avoid:
- Repeating every piece of evidence
- Summarizing each document separately
- Speculating beyond the evidence
- Omitting source attribution for claims
"""
        
        response = llm.invoke(prompt)

        return response.content

    # TOOL 7: RESEARCH MEMORY

    @tool
    def research_memory_tool(query: str):
        """
        Search previous research findings stored in long-term memory.

        Use this tool when the user asks:
        - what was concluded previously
        - previous research
        - historical findings
        - remembered insights
        - prior analyses
        """

        memory = get_memory_content()

        if not memory.strip():
            return "No research memory available."

        return f"""
PREVIOUS RESEARCH MEMORY

The following information comes from prior completed research analyses.

{memory}
"""
    
    # TOOL 8: SANDBOX EXECUTE
    @tool
    def sandbox_execute(command: str) -> str:
        """
        Run a shell command inside the Modal sandbox.

        Use this tool for ALL OfficeCLI document generation commands.
        Use when the user asks to create presentations, reports,
        spreadsheets, or PDF documents.

        Always:
        - Create output directory first: mkdir -p /workspace/output

        - IMPORTANT FOR NEW OFFICE DOCUMENTS:
          For a brand new Office document (.pptx, .docx, .xlsx):
          1. Create the Office document first using: officecli create /workspace/output/<filename>.<extension>
          2. After the document exists, use OfficeCLI batch commands to populate or edit it.
          3. Never use `touch` to create Office documents. A touched file is a 0-byte file and is not a valid Office document.
          4. If editing an existing Office document, do NOT recreate it. Modify the existing document directly.
          
        - Save files to /workspace/output/<filename>.<format>
        - Check exit_code == 0 in the response before continuing
        - Follow the OfficeCLI skill file for exact command sequences

        Supported formats: pptx, docx, xlsx, pdf

        Args:
            command: shell command to run in the sandbox

        Returns:
            exit_code and output from the command
        """
        import os
        from app.services.sandbox.session_store import (
            get_backend as _get_backend,
            record_output_files,
        )

        if os.getenv("USE_MODAL_SANDBOX", "false").lower() != "true":
            return "exit_code=1\noutput=Sandbox is disabled (USE_MODAL_SANDBOX=false)"

        backend = _get_backend(thread_id)
        output_state_before = _get_output_file_state(backend)

        # OfficeCLI is installed in /root/.local/bin inside Modal sandboxes.
        # Ensure it is available on PATH for every command.
        command = f"export PATH=/root/.local/bin:$PATH && {command}"

        print(f"EXECUTING: {command}")
        result = backend.execute(command)
        output_state_after = _get_output_file_state(backend)
        changed_output_files = [
            filename
            for filename, modified_at in output_state_after.items()
            if output_state_before.get(filename) != modified_at
        ]

        if changed_output_files:
            record_output_files(
                thread_id,
                [f"/workspace/output/{filename}" for filename in changed_output_files],
            )

        return (
            f"exit_code={result.exit_code}\n"
            f"output={result.output}\n"
            f"output_dir_listing={chr(10).join(sorted(output_state_after.keys()))}\n"
            f"tracked_output_files={json.dumps(sorted(changed_output_files))}"
        )
    
    @tool
    def get_current_document() -> str:
        """

        Return the active Office document for the current conversation.

        Use this tool ONLY when the user wants to edit, update, revise,
        continue, append to, shorten, expand, or otherwise modify an
        existing Office document.

        Do NOT use this tool when creating a completely new document.

        """

        from app.services.sandbox.session_store import get_current_document

        document = get_current_document(thread_id)

        if document is None:
            return "No current working document exists."

        return (
            f"Current document:\n"
            f"Filename: {document.filename}\n"
            f"Type: {document.file_type}\n"
            f"Path: {document.path}"
        )
    
    @tool
    def inspect_runtime() -> str:
        """Debug the runtime passed to StoreBackend."""

        from langgraph.runtime import get_runtime

        rt = get_runtime()

        return (
            f"type={type(rt)}\n"
            f"attrs={dir(rt)}\n"
            f"config={getattr(rt, 'config', None)}\n"
            f"context={getattr(rt, 'context', None)}\n"
        )
        

    # Return all tools for the agent
    return [
        search_documents_tool,
        summarize_document_tool,
        compare_documents_tool,
        identify_trends_tool,
        risk_analysis_tool,
        deep_research_tool,
        research_memory_tool,
        sandbox_execute,
        get_current_document,
        inspect_runtime
    ]

def get_deep_rag_agent(
    document_id: str | None = None,
    document_ids: list[str] | None = None,
    thread_id: str = "default"
):
    """
    Create a Deep Agent specialized for multi-step analytical research.
    
    This agent uses multiple specialized tools to approach complex questions
    through planning and decomposition:
    
    1. Gather evidence (search_documents, summarize)
    2. Analyze from multiple perspectives (compare, trends, risks)
    3. Synthesize into strategic insights (deep_research for synthesis)
    
    The agent decides which tools to use and in what order based on:
    - Question complexity
    - Need for comparison, trend analysis, or risk assessment
    - Synthesis requirements
    
    This architecture naturally encourages multi-step planning and helps
    the agent avoid hallucination by using specialized tools for each
    analytical dimension.
    """
    llm = ChatBedrockConverse(
        model="global.anthropic.claude-haiku-4-5-20251001-v1:0",
        region_name=os.getenv("AWS_REGION"),
    )

    tools = create_tools(
        llm=llm,
        document_id=document_id,
        document_ids=document_ids,
        thread_id=thread_id
    )

    redis_client = Redis.from_url(
        os.getenv("REDIS_URL", "redis://rag-redis:6379")
    )

    redis_store = RedisStore(redis_client)

    # Preserve current FilesystemBackend path behavior explicitly so future
    backend = FilesystemBackend(root_dir="/app", virtual_mode=False)

    agent = create_deep_agent(
        model=llm,
        tools=tools,
        backend=backend,
        skills=[
            "app/skills"
        ],
        
        memory=["app/memory/research_history.md"],
        checkpointer=memory_checkpointer,
        system_prompt="""
You are an expert document analyst and strategic research agent.

Your role is to help users understand complex information by performing
systematic, multi-perspective analysis on retrieved evidence.

========================================
AVAILABLE TOOLS
========================================

RETRIEVAL & OVERVIEW:
- search_documents_tool: Use for factual questions, lookups, and direct evidence
- summarize_document_tool: Use for summaries and document overviews

SPECIALIZED ANALYSIS (use these to analyze from different angles):
- compare_documents_tool: Use when comparing documents, viewpoints, opinions, 
  forecasts, or perspectives. Identifies agreements, disagreements, and 
  complementary information.
- identify_trends_tool: Use when looking for recurring patterns, trends, 
  themes, or emerging signals. Identifies cause-and-effect patterns.
- risk_analysis_tool: Use when assessing risks, uncertainty, contradictions, 
  weaknesses, or confidence levels. Identifies gaps and potential issues.

SYNTHESIS:
- deep_research_tool: Use for comprehensive executive-level synthesis, 
  strategic reviews, investment analysis, or multi-step investigations after 
  you've gathered specialized analyses.

MEMORY:
- research_memory_tool: Use when the user asks about previous research,
  remembered insights, prior analyses, historical findings, or what was
  concluded before.

WORKING DOCUMENT STATE:
- get_current_document: Use when the user asks to edit, modify, update,
  revise, continue, append, shorten, expand, reformat, or otherwise
  change a previously generated Office document.
- Call this tool before performing document modifications unless the
  user explicitly provides a different document.
- If a current working document exists, modify that document instead
  of creating a new one.
- If no current working document exists, inform the user and ask them
  to generate or specify a document first.  

DOCUMENT GENERATION:
When the user asks to create, generate, or export any document
(PowerPoint presentation, Word report, Excel spreadsheet, PDF):
- Use sandbox_execute tool directly to run OfficeCLI commands in the sandbox
- Follow the OfficeCLI skill file for exact command sequences
- Save all generated files to /workspace/output/
- Create output directory first: sandbox_execute("mkdir -p /workspace/output")
- Load the right skill first: sandbox_execute("officecli load_skill pptx") etc.
- Check exit_code == 0 after every command
- Tell the user their document is ready when done
- Supported formats: pptx, docx, xlsx, pdf
- You decide the structure, content, and layout freely based on the request

========================================
MULTI-STEP REASONING FOR COMPLEX QUESTIONS
========================================

For simple factual questions:
→ Use search_documents_tool directly

For analytical questions, use a systematic approach:

1. CLARIFY: Understand what analysis is needed (comparison? trends? risks?)

2. GATHER: Retrieve relevant evidence
   - Use search_documents_tool or summarize_document_tool first
   - Get context before specializing
   - Use research_memory_tool if the user asks about prior conclusions or
     remembered research

3. ANALYZE (pick which tools based on question):
   - Comparing viewpoints? → Use compare_documents_tool
   - Looking for patterns? → Use identify_trends_tool
   - Assessing risks/certainty? → Use risk_analysis_tool
   - Need multiple perspectives? → Use 2-3 tools in sequence

4. SYNTHESIZE: Use deep_research_tool to pull findings together
   - This is where you create executive summary
   - This is where you make strategic recommendations
   - This is where you synthesize across specialized analyses

5. CONCLUDE: Present findings with clear source attribution

6. DOCUMENT MODIFICATION (only when editing existing Office documents):
   - Determine whether the user wants to modify an existing document
     rather than create a new one.
   - Call get_current_document to identify the active working document.
   - If a document exists, open and modify that document using
     OfficeCLI.
   - Preserve the existing content unless the user explicitly requests
     replacement.

========================================
QUALITY STANDARDS
========================================

1. EVIDENCE-BASED REASONING
   - Base ALL conclusions ONLY on retrieved evidence
   - Cite sources explicitly (document name, key quotes)
   - Do NOT hallucinate or speculate beyond evidence
   - Acknowledge uncertainty when evidence is limited

2. STRUCTURED ANALYSIS
   - For complex questions, use the multi-step approach above
   - Plan before diving into retrieval
   - Use multiple tools to analyze from different angles
   - Synthesize across specialized analyses rather than repeating each

3. SOURCE ATTRIBUTION
   - ALWAYS attribute claims to sources
   - Include document names and specific evidence
   - Distinguish between direct quotes and synthesis
   - When sources conflict, acknowledge and explain

4. CONFIDENCE & LIMITATIONS
   - Estimate confidence in findings
   - Report uncertainty levels
   - Explicitly acknowledge gaps in evidence
   - Distinguish inference from direct evidence

5. TOOL SELECTION
   - Choose the right tool for the task
   - Don't over-retrieve (use appropriate top_k)
   - Avoid redundant tool calls
   - Use specialized tools before synthesis

6. DOCUMENT CONTINUITY
   - Reuse the current working Office document whenever the user's
     request is a continuation or revision.
   - Avoid creating duplicate documents when an existing working
     document can be updated instead.

========================================
STRATEGIC INSIGHTS
========================================

Your synthesis should produce:
- Executive-level conclusions (not just evidence summaries)
- Strategic implications and opportunities
- Forward-looking recommendations
- Clear risk assessment
- Actionable insights

Avoid:
- Repeating every piece of evidence verbatim
- Summarizing each document separately
- Generic conclusions that don't synthesize
- Omitting source attribution
- Speculating beyond the evidence

========================================
EXAMPLE WORKFLOW
========================================

User Question: "What are the key investment risks in gold mining over the next 5 years?"

Your Approach:
1. search_documents_tool("gold mining investment risks 5 year forecast")
   → Get overview of what information exists
2. identify_trends_tool("gold mining industry trends and market direction")
   → Find patterns and emerging signals
3. risk_analysis_tool("gold mining investment risks and uncertainties")
   → Analyze specific risks and confidence levels
4. deep_research_tool("comprehensive gold mining investment analysis with risks and opportunities")
   → Synthesize into final strategic assessment

Result: Executive-level conclusion with:
- Key risks identified
- Confidence levels
- Strategic implications
- Source-attributed evidence
- Recommendations

========================================

When no relevant information is found, clearly say so.

SANDBOX EXECUTION RULES:
- When running multiple OfficeCLI commands, batch them using officecli batch
  to reduce the number of execute calls
- Always complete document generation in as few execute calls as possible
- Use officecli batch for multi-step document creation:

  sandbox_execute('''echo '[
    {"command":"add","path":"/","type":"slide","props":{"title":"Slide 1"}},
    {"command":"add","path":"/slide[1]","type":"shape","props":{"text":"Content"}}
  ]' | officecli batch /workspace/output/file.pptx''')

- Prefer batch over individual commands whenever adding multiple elements
""",
        middleware=[
            BedrockPromptCachingMiddleware(
                ttl="1h",
                min_messages_to_cache=0,
                unsupported_model_behavior="warn",
            )
        ],

        debug=True
        
    )

    return agent
