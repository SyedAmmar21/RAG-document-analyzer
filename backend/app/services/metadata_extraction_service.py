import json
import re

from langchain_openai import ChatOpenAI

from app.prompts.metadata_prompt import build_metadata_prompt

llm = ChatOpenAI(model="gpt-5.4-nano")

METADATA_FIELDS = [
    "title",
    "published_date",
    "focus",
    "entities",
    "economic_indicators",
    "regions",
]

ECONOMIC_INDICATORS = {
    "CPI": r"\bCPI\b|\bconsumer price index\b",
    "PPI": r"\bPPI\b|\bproducer price index\b",
    "GDP": r"\bGDP\b|\bgross domestic product\b",
    "inflation": r"\binflation\b|\binflationary\b",
    "unemployment": r"\bunemployment\b|\bjobless\b|\blabor market\b|\blabour market\b",
    "interest rates": r"\binterest rates?\b|\brate cuts?\b|\brate hikes?\b|\bmonetary policy\b",
}

ENTITIES = {
    "Federal Reserve": r"\bFederal Reserve\b|\bFed\b|\bFOMC\b",
    "ECB": r"\bECB\b|\bEuropean Central Bank\b",
    "BOJ": r"\bBOJ\b|\bBank of Japan\b",
    "PBOC": r"\bPBOC\b|\bPeople'?s Bank of China\b",
    "US Treasury": r"\bUS Treasury\b|\bU\.S\. Treasury\b|\bTreasury yields?\b",
}

REGIONS = {
    "United States": r"\bUnited States\b|\bU\.S\.\b|\bAmerica\b",
    "China": r"\bChina\b|\bChinese\b",
    "Europe": r"\bEurope\b|\bEurozone\b|\bEuropean\b",
    "Middle East": r"\bMiddle East\b|\bGaza\b|\bIsrael\b|\bIran\b|\bSaudi Arabia\b",
    "Russia": r"\bRussia\b|\bRussian\b",
}

DATE_PATTERNS = [
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
    r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}/\d{1,2}/\d{4}\b",
]


def _excerpt(text: str):
    return (text or "")[:2000]


def _find_first_date(text: str):
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _match_keywords(text: str, patterns: dict):
    values = []

    for label, pattern in patterns.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            values.append(label)

    return values or None


def _normalize_list(value):
    if not value:
        return []

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if not isinstance(value, list):
        return []

    return [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]


def _merge_lists(*values):
    merged = []
    seen = set()

    for value in values:
        for item in _normalize_list(value):
            key = item.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)

    return merged or None


def _run_rule_based_extraction(text: str):
    return {
        "published_date": _find_first_date(text),
        "economic_indicators": _match_keywords(text, ECONOMIC_INDICATORS),
        "entities": _match_keywords(text, ENTITIES),
        "regions": _match_keywords(text, REGIONS),
    }


def _run_llm_extraction(text: str):
    prompt = build_metadata_prompt(text)

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        parsed = json.loads(json_match.group(0) if json_match else content)
    except Exception:
        return {
            "title": None,
            "focus": None,
            "entities": None,
            "economic_indicators": None,
            "regions": None,
        }

    return {
        "title": parsed.get("title") or None,
        "focus": parsed.get("focus") or None,
        "entities": _normalize_list(parsed.get("entities")) or None,
        "economic_indicators": _normalize_list(parsed.get("economic_indicators")) or None,
        "regions": _normalize_list(parsed.get("regions")) or None,
    }


def extract_metadata(extracted_text: str):
    text = _excerpt(extracted_text)
    rule_metadata = _run_rule_based_extraction(text)
    llm_metadata = _run_llm_extraction(text)

    return {
        "title": llm_metadata["title"],
        "published_date": rule_metadata["published_date"],
        "focus": llm_metadata["focus"],
        "entities": _merge_lists(rule_metadata["entities"], llm_metadata["entities"]),
        "economic_indicators": _merge_lists(
            rule_metadata["economic_indicators"],
            llm_metadata["economic_indicators"]
        ),
        "regions": _merge_lists(rule_metadata["regions"], llm_metadata["regions"]),
    }
