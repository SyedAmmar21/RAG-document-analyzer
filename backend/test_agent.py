# test_agent.py

from app.services.rag_agent_service import get_deep_rag_agent

agent = get_deep_rag_agent()

response = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": """
Create a PowerPoint presentation.

Title:
AI Research Report

Slides:
- Executive Summary
- Key Findings
- Recommendations
"""
            }
        ]
    }
)

print(response)