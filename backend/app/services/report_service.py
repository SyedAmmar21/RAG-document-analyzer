from langchain_openai import ChatOpenAI


def create_report(
    query: str,
    research_output: str
):
    """
    Convert research output into a structured executive report.
    """

    llm = ChatOpenAI(model="gpt-5.4-nano")

    prompt = f"""
You are an executive report writer.

Convert the research into a professional report.

Use EXACTLY this structure:

# Report Title

## Executive Summary

## Key Findings
- Bullet points

## Trend Analysis

## Risk Assessment

## Supporting Evidence

## Strategic Recommendations

## Confidence Assessment

## Conclusion

Rules:
- Be concise
- Use markdown
- Base everything ONLY on the research provided
- Do not invent facts
- Keep the report professional

Original Question:
{query}

Research:
{research_output}
"""

    response = llm.invoke(prompt)

    return response.content