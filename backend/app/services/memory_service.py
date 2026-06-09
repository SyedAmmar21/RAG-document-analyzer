from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI

MEMORY_FILE = Path("app/memory/research_history.md")


def create_memory_entry(
    query: str,
    answer: str
):
    """
    Convert a long research report into a concise memory entry.
    """

    llm = ChatOpenAI(model="gpt-5.4-nano")

    prompt = f"""
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

    response = llm.invoke(prompt)

    return response.content


def save_memory_entry(memory_entry: str):
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