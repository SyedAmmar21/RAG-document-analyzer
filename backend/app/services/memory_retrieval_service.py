from pathlib import Path

MEMORY_FILE = Path("app/memory/research_history.md")


def get_memory_content() -> str:
    """
    Load all stored research memory.
    """

    if not MEMORY_FILE.exists():
        return "No research memory available."

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return f.read()