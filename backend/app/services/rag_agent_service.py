from multiprocessing import context
from langchain.tools import tool
from deepagents import create_deep_agent
from langchain_aws import ChatBedrockConverse
import json
import re
import os
from collections import defaultdict
from pathlib import PurePosixPath

from app.services.retrieval_service import search_documents
from app.services.redis_store_service import search_research_memories
from langchain_aws.middleware.prompt_caching import BedrockPromptCachingMiddleware
from langgraph.checkpoint.memory import MemorySaver
from deepagents.backends import (
    FilesystemBackend,
    CompositeBackend,
    StoreBackend,
)
from app.services.sandbox.backend_contract import (
    build_command_preamble,
    sandbox_enabled,
)
from app.services.presentation_workflow import PresentationWorkflow

from app.services.redis_store_service import get_redis_store

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



def create_tools(
    llm,
    document_id=None,
    document_ids=None,
    thread_id="default",
    presentation_workflow: PresentationWorkflow | None = None,
):
    presentation_workflow = presentation_workflow or PresentationWorkflow()

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
    Retrieve long-term research memories stored in Redis.

    ALWAYS use this tool BEFORE answering if the user asks about:

    - previous conversations
    - what we discussed before
    - what we concluded previously
    - what you remember
    - remembered research
    - previous findings
    - prior analyses
    - historical research
    - "last time"
    - "earlier"
    - "before"

    Do NOT answer these questions from conversation memory alone.
    Always search the stored research memories first.
        """

        memories = search_research_memories(
            query=query,
            limit=5,
        )

        if not memories:
            return "No relevant research memory found."

        output = []

        for memory in memories:
            value = memory.value

            output.append(
                f"""
    Question:
    {value.get("query")}

    Summary:
    {value.get("summary")}
    """
            )

        return (
            "PREVIOUS RESEARCH MEMORY\n\n"
            + "\n\n----------------------\n\n".join(output)
        )
    
    # TOOL 8: SANDBOX EXECUTE
    @tool
    def sandbox_execute(command: str) -> str:
        """

        Execute a shell command inside the configured sandbox environment.

        Use this tool whenever a task requires shell execution, including
        OfficeCLI document generation.

        For Office document operations:

        - Follow the OfficeCLI skill as the authoritative workflow.
        - Do not invent OfficeCLI commands, skill names, JSON fields,
        selectors, or properties.
        - Use only officially supported OfficeCLI commands.
        - If OfficeCLI syntax is uncertain, consult OfficeCLI help before
        executing another OfficeCLI command.
        - Create new Office documents using the official OfficeCLI workflow.
        - Modify existing Office documents rather than recreating them.
        - Save generated documents to /workspace/output/.
        - Prefer officecli batch when multiple OfficeCLI operations can be
        executed together.
        - Minimize the number of sandbox executions whenever practical.
        - For a PowerPoint request, OfficeCLI execution is unavailable until
          the presentation plan has been validated, official recipe guidance
          has been loaded, and every slide has a selected recipe.
        - If an OfficeCLI command fails, repair only the failed command
        instead of restarting the entire workflow.

        The sandbox runs the provided shell command inside a standardized
        shell environment. It does not interpret or modify OfficeCLI syntax.

        Args:
            command: Shell command to execute.

        Returns:
            Sandbox execution result containing:
            - exit_code
            - stdout
            - stderr
            - output (stdout + stderr)
        """
       
        import os
        from app.services.sandbox.session_store import (
            get_current_document as _get_current_document,
            get_backend as _get_backend,
            record_output_files,
        )

        try:
            presentation_workflow.assert_officecli_generation_allowed(command)
        except ValueError as exc:
            return f"exit_code=1\nstdout=\nstderr={exc}\noutput={exc}"

        if not sandbox_enabled():
            return "exit_code=1\nstdout=\nstderr=Sandbox is disabled\noutput=Sandbox is disabled"

        backend = _get_backend(thread_id)
        output_state_before = _get_output_file_state(backend)

        command = f"{build_command_preamble()}{command}"

        print(f"EXECUTING: {command}")
        result = backend.execute(command)
        output_state_after = _get_output_file_state(backend)
        changed_output_files = [
            filename
            for filename, modified_at in output_state_after.items()
            if output_state_before.get(filename) != modified_at
        ]

        if result.exit_code == 0 and "officecli" in command.lower() and not changed_output_files:
            current_document = _get_current_document(thread_id)
            if current_document is not None:
                current_filename = PurePosixPath(current_document.path).name
                if current_filename:
                    changed_output_files.append(current_filename)

        if changed_output_files:
            record_output_files(
                thread_id,
                [f"/workspace/output/{filename}" for filename in changed_output_files],
            )

        
        import json
        import re

        if "officecli batch" in command:

            print("=" * 80)
            print("VALIDATING OFFICECLI BATCH")
            print("=" * 80)

            payload = None

            # heredoc
            m = re.search(
                r"<<'EOF'\s*(.*?)\s*EOF",
                command,
                flags=re.DOTALL,
            )

            if m:
                payload = m.group(1)

            # echo '[ ... ]'
            if payload is None:
                m = re.search(
                    r"echo\s+'(.*?)'\s*\|\s*officecli\s+batch",
                    command,
                    flags=re.DOTALL,
                )

                if m:
                    payload = m.group(1)

            if payload is None:
                print("No batch JSON found.")

            else:

                print("Batch JSON:")
                print(payload)
                payload = payload.strip()

                if not payload:
                    print("Batch JSON was empty; skipping local validation.")
                else:
                    try:
                        json.loads(payload)
                        print("✓ JSON VALID")

                    except Exception as e:

                        print("✗ JSON INVALID")
                        print(e)

                        # Keep this validator best-effort. Its job is to help
                        # debug malformed OfficeCLI batch payloads, not to mask
                        # the actual sandbox execution result with a secondary
                        # JSON parsing exception from this wrapper.
                        if result.exit_code != 0:
                            result.stderr = (
                                f"{result.stderr}\n"
                                f"Local batch JSON validation failed: {e}"
                            ).strip()
                            result.output = (
                                f"{result.output}\n"
                                f"Local batch JSON validation failed: {e}"
                            ).strip()

        return (
            f"exit_code={result.exit_code}\n"
            f"stdout={result.stdout}\n"
            f"stderr={result.stderr}\n"
            f"output={result.output}\n"
            f"output_dir_listing={chr(10).join(sorted(output_state_after.keys()))}\n"
            f"tracked_output_files={json.dumps(sorted(changed_output_files))}"
        )

    @tool
    def create_presentation_plan(plan_json: str) -> str:
        """Validate and store the mandatory slide-by-slide presentation plan.

        Call this before *any* OfficeCLI command for a presentation. The input
        must be JSON with this shape:
        {
          "deck": {
            "deck_type": "executive report",
            "audience": "leadership team",
            "objective": "make a decision",
            "visual_identity": "blue consulting",
            "motif": "numbered insight cards",
            "officecli_skill": "pptx"
          },
          "slides": [{
            "slide_number": 1,
            "title": "...",
            "purpose": "...",
            "archetype": "hero",
            "primary_visual": "...",
            "supporting_elements": ["..."],
            "information_density": "executive",
            "recipe_goal": "hero / cover recipe from the loaded PPTX skill"
          }]
        }

        The plan is an implementation contract, not a user-facing outline.
        Do not include OfficeCLI commands. A later tool retrieves the official
        PPTX skill and a separate call binds every slide to an exact recipe.
        """
        try:
            plan = presentation_workflow.register_plan(plan_json)
        except ValueError as exc:
            return f"PLAN_INVALID: {exc}"

        return (
            "PLAN_ACCEPTED. OfficeCLI remains locked. Next call "
            "load_presentation_recipe_guidance, then select recipes for every slide.\n"
            f"Deck: {plan.deck.deck_type}; slides: {len(plan.slides)}\n"
            f"{presentation_workflow.plan_summary()}"
        )

    @tool
    def load_presentation_recipe_guidance() -> str:
        """Load the official OfficeCLI PPTX or pitch-deck skill after planning.

        This is the only recipe retrieval step. Use the returned official skill
        content to select a recipe for each planned slide; do not invent layout
        commands or copy recipe documentation into prompts. This tool does not
        allow PPTX generation yet.
        """
        try:
            officecli_skill = presentation_workflow.recipe_skill_to_load()
        except ValueError as exc:
            return f"RECIPE_GUIDANCE_LOCKED: {exc}"

        if not sandbox_enabled():
            return "RECIPE_GUIDANCE_FAILED: Sandbox is disabled"

        from app.services.sandbox.session_store import get_backend as _get_backend

        backend = _get_backend(thread_id)
        result = backend.execute(
            f"{build_command_preamble()}officecli load_skill {officecli_skill}"
        )
        if result.exit_code != 0:
            return (
                "RECIPE_GUIDANCE_FAILED: "
                f"{result.stderr or result.stdout or result.output}"
            )

        presentation_workflow.mark_recipe_guidance_loaded()
        return (
            "OFFICIAL_RECIPE_GUIDANCE_LOADED. Select an exact official recipe "
            "for every slide using select_presentation_recipes before generating.\n\n"
            f"{result.output}"
        )

    @tool
    def select_presentation_recipes(selections_json: str) -> str:
        """Bind each planned slide to an exact recipe from the loaded OfficeCLI skill.

        Input JSON: {"selections": [{"slide_number": 1,
        "officecli_recipe": "exact recipe name or reference returned by load_presentation_recipe_guidance",
        "rationale": "why this recipe implements the planned archetype"}]}.

        This requires one and only one selection for every planned slide. After
        success, OfficeCLI generation may implement the already-selected plan;
        it must not reconsider slide type or invent a new layout.
        """
        try:
            selections = presentation_workflow.register_recipe_selections(selections_json)
        except ValueError as exc:
            return f"RECIPE_SELECTION_INVALID: {exc}"

        summary = "\n".join(
            f"Slide {number}: {selection.officecli_recipe}"
            for number, selection in sorted(selections.items())
        )
        return (
            "RECIPE_SELECTION_ACCEPTED. OfficeCLI generation is now unlocked. "
            "Implement this contract exactly, then call qa_presentation.\n"
            f"{summary}"
        )

    @tool
    def qa_presentation(presentation_path: str) -> str:
        """Run required structural and issue QA on a generated presentation.

        Call only after generating the PPTX at /workspace/output/<filename>.pptx.
        It runs official OfficeCLI validation and issue inspection. If either
        fails, repair the presentation with the selected recipe contract and
        run this tool again before delivery.
        """
        try:
            checked_path = presentation_workflow.prepare_qa(presentation_path)
        except ValueError as exc:
            return f"PRESENTATION_QA_LOCKED: {exc}"

        if not sandbox_enabled():
            return "PRESENTATION_QA_FAILED: Sandbox is disabled"

        from app.services.sandbox.session_store import get_backend as _get_backend

        backend = _get_backend(thread_id)
        command_prefix = build_command_preamble()
        validation = backend.execute(f"{command_prefix}officecli validate {checked_path}")
        issues = backend.execute(f"{command_prefix}officecli view {checked_path} issues")
        if validation.exit_code != 0 or issues.exit_code != 0:
            return (
                "PRESENTATION_QA_FAILED. Repair only the reported problem and retry.\n"
                f"validate: {validation.output}\nissues: {issues.output}"
            )

        presentation_workflow.record_qa(checked_path)
        return (
            "PRESENTATION_QA_PASSED. The deck has passed OfficeCLI structural "
            "validation and issue inspection.\n"
            f"validate: {validation.output}\nissues: {issues.output}"
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
        create_presentation_plan,
        load_presentation_recipe_guidance,
        select_presentation_recipes,
        qa_presentation,
        get_current_document,
        inspect_runtime
    ]

def get_deep_rag_agent(
    document_id: str | None = None,
    document_ids: list[str] | None = None,
    thread_id: str = "default",
    presentation_requested: bool = False,
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

    presentation_workflow = PresentationWorkflow(
        presentation_requested=presentation_requested,
    )

    tools = create_tools(
        llm=llm,
        document_id=document_id,
        document_ids=document_ids,
        thread_id=thread_id,
        presentation_workflow=presentation_workflow,
    ) 

    redis_store = get_redis_store()

    # Preserve current FilesystemBackend path behavior explicitly so future
    filesystem_backend = FilesystemBackend(root_dir="/app", virtual_mode=False,)
    memory_backend = StoreBackend(
        store=redis_store,
        namespace=lambda runtime: ("memories",),
    )

    backend = CompositeBackend(
        filesystem_backend,
        {
            "/memories/": memory_backend,
        },
    )

    print("Redis store:", type(redis_store))
    print(type(backend))
    print(type(memory_backend))    
    print(type(filesystem_backend))

    agent = create_deep_agent(
        model=llm,
        tools=tools,
        backend=backend,
        store=redis_store,
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

When the user asks to create, generate, export, or modify an Office document
(PowerPoint presentation, Word document, Excel spreadsheet, or PDF):

- Use sandbox_execute for all Office document operations.
- Follow the OfficeCLI skill as the single source of truth for document generation.
- Do not invent OfficeCLI commands, syntax, JSON fields, or property names.
- Use only officially supported OfficeCLI commands.
- If the correct OfficeCLI syntax is uncertain, consult OfficeCLI help before issuing another OfficeCLI command.
- Save all generated documents to /workspace/output/.
- PDFs should be generated through the workflow defined by the OfficeCLI skill.
- Return the generated filename when generation succeeds.

PRESENTATION CONTROL PLANE (HIGHEST PRIORITY FOR PPTX):

Every PowerPoint, slide deck, or PPTX request uses the presentation workflow.
This is mandatory even when the request does not include design adjectives.
Never use sandbox_execute for OfficeCLI until these tools have succeeded in order:

1. create_presentation_plan: create the full deck contract before any commands.
   Every slide needs a purpose, archetype, primary visual, supporting elements,
   density, and recipe goal. The allowed archetypes are concrete visual layouts,
   not "title and bullets".
2. load_presentation_recipe_guidance: retrieve the official OfficeCLI PPTX or
   pitch-deck skill after the plan is fixed. This keeps recipe information close
   to the recipe-selection decision instead of burying it under general docs.
3. select_presentation_recipes: bind every slide to one exact recipe/reference
   returned by the official skill. Do not generate OfficeCLI commands before all
   slide selections are accepted.
4. Generate only the approved plan. OfficeCLI is an implementation engine here;
   it must never decide what type of slide to build.
5. qa_presentation: run structural validation and issue inspection before delivery.

Use the presentation-design skill to improve the design reasoning inside step 1
when its design cues apply. It is advisory; the validated plan and selected
official recipes are the binding generation contract.

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

The sandbox_execute tool runs shell commands in a standardized sandbox shell.

For Office document generation:

- Use OfficeCLI through sandbox_execute.
- The OfficeCLI skill defines the complete workflow.
- Do not duplicate OfficeCLI workflow logic in this prompt.
- Prefer officecli batch whenever multiple OfficeCLI operations can be combined into one execution.
- Minimize the number of sandbox_execute calls whenever practical.
- Never invent OfficeCLI commands, skill names, JSON fields, selectors, or properties.
- If OfficeCLI returns an error, repair only the failed command rather than restarting the entire document generation process.
- Stop issuing OfficeCLI commands once the requested document has been successfully generated.
""",
        middleware=[
            BedrockPromptCachingMiddleware(
                ttl="5m",
                min_messages_to_cache=0,
                unsupported_model_behavior="warn",
            )
        ],

        debug=True
        
    )

    return agent
