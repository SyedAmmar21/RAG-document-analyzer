def build_metadata_prompt(document_text: str):
    return f"""
You extract concise metadata from financial and news documents related to gold market analysis.

Return ONLY valid JSON with these exact keys:
{{
  "title": string or null,
  "focus": string or null,
  "entities": array of strings or null,
  "economic_indicators": array of strings or null,
  "regions": array of strings or null
}}

Rules:
- "title" is the document title or headline if one is visible.
- "focus" is a concise semantic description of the article's financial-market focus.
- Make "focus" financial-context aware, especially for gold, inflation, central banks, currency, rates, geopolitical risk, and macroeconomic drivers.
- "entities" should include relevant central banks, government bodies, market institutions, companies, or named organizations.
- "economic_indicators" should include macro or market indicators that matter to the document, including country-specific indicators such as OPR, ringgit, bond yields, trade balance, gold reserves, or PMI when relevant.
- "regions" should include countries, regions, or geopolitical areas that are materially relevant to the document.
- Use null if unavailable.
- Keep arrays concise. Prefer 1 to 6 high-signal items.
- Do not include markdown, evidence, explanations, or extra keys.

Document excerpt:
{document_text}
"""
