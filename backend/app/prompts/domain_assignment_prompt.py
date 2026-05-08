import json
from typing import Dict, List


def build_domain_assignment_prompt(metadata: Dict, domains: List[Dict]):
    domain_context = "\n".join(
        f"- {domain['name']}: {domain.get('description') or 'No description'}"
        for domain in domains
    )

    metadata_context = json.dumps(metadata, ensure_ascii=False, indent=2)

    return f"""
You assign financial/news documents to semantic knowledge domains.

Domains are conceptual context clusters, not folders.
Choose the single closest domain based on the document metadata.

Available domains:
{domain_context}

Document metadata:
{metadata_context}

Return ONLY valid JSON with these exact keys:
{{
  "suggested_domain": string,
  "confidence": number
}}

Rules:
- selected domain must exactly match one of the available domain names.
- confidence must be between 0 and 1.
- use title, focus, entities, economic_indicators, and regions as primary semantic signals.
- do not include markdown, reasoning, or extra keys.
"""
