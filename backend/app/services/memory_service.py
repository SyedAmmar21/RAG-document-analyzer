from datetime import datetime
from pathlib import Path
from app.services.redis_store_service import save_research_memory
from langchain_openai import ChatOpenAI

MEMORY_FILE = Path("app/memory/research_history.md")


def create_memory_entry(
    query: str,
    answer: str
):
    """
    Determine whether a research result deserves long-term memory.
    If yes, create a compact memory entry.
    If not, return None.
    """

    llm = ChatOpenAI(model="gpt-5.4-nano")

    evaluation_prompt = f"""
You are deciding whether a research result deserves long-term memory.

SAVE only if the result contains:
- strategic analysis
- trends
- comparisons
- risks
- investment insights
- executive conclusions
- important findings that may be useful later

DO NOT SAVE:
- simple factual lookups
- basic summaries
- short Q&A
- document navigation questions
- trivial information

Respond ONLY:

YES

or

NO

Question:
{query}

Answer:
{answer}
"""

    evaluation = llm.invoke(
        evaluation_prompt
    ).content.strip().upper()

    if evaluation != "YES":
        print("Memory skipped: not important enough.")
        return None

    print("Memory approved for storage.")

    summary_prompt = f"""
You are creating long-term research memory.

Summarize the research below into a compact memory entry.

Keep only:

- Topic
- Key Findings (max 5 bullets)
- Risks (max 5 bullets)
- Confidence Level
- Final Conclusion

Keep under 200 words.

Question:
{query}

Research Output:
{answer}
"""

    memory_entry = llm.invoke(
        summary_prompt
    ).content

    return memory_entry

def save_memory_entry(query: str, memory_entry: str):
    print("MEMORY FILE:", MEMORY_FILE.resolve())
    """
    Append a summarized memory entry to research history.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(
            f"""

## Research Entry

Date: {timestamp}

{memory_entry}

---

"""
        )
    # Save to Redis as well
    save_research_memory(
        query=query,
        summary=memory_entry,
    )