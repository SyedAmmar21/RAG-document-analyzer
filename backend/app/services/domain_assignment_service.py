import json
import re
from typing import Dict, List

from langchain_openai import ChatOpenAI

from app.prompts.domain_assignment_prompt import build_domain_assignment_prompt

llm = ChatOpenAI(model="gpt-5.4-nano")


def _confidence(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.5

    return max(0.0, min(1.0, score))


def assign_domain(metadata: Dict, domains: List[Dict]):
    if not domains:
        return {
            "suggested_domain": None,
            "confidence": 0.0,
        }

    prompt = build_domain_assignment_prompt(metadata, domains)

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        parsed = json.loads(json_match.group(0) if json_match else content)
    except Exception:
        return {
            "suggested_domain": domains[0]["name"],
            "confidence": 0.5,
        }

    domain_names = {domain["name"].casefold(): domain["name"] for domain in domains}
    suggested = parsed.get("suggested_domain")
    matched_domain = domain_names.get(suggested.casefold()) if isinstance(suggested, str) else None

    return {
        "suggested_domain": matched_domain or domains[0]["name"],
        "confidence": _confidence(parsed.get("confidence")),
    }
