from app.services.rag_agent_service import get_rag_agent

agent = get_rag_agent()

query = "What is AI?"

response = agent.invoke({
    "messages": [
        {"role": "user", "content": query}
    ]
})

print("\n--- AGENT RESPONSE ---\n")
print(response["messages"][-1].content)