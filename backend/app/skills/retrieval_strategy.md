# Retrieval Strategy Skill

## Purpose

Teach the Deep Agent to strategically choose between retrieval tools based on user intent.

This skill helps the agent decide:
- **When to use search_documents_tool**: For factual lookups and quick answers
- **When to use deep_research_tool**: For comprehensive analysis and synthesis
- **How to combine tools effectively**: Multi-step reasoning strategies

## Tool Selection Framework

### Use `search_documents_tool` when:

The user is asking for:

1. **Direct Factual Questions**
   - "What is the gold price in the document?"
   - "Who is the CEO of company X?"
   - "What date did this event occur?"
   - → Use: `search_documents_tool` (fast retrieval)

2. **Quick Summaries**
   - "Summarize this document briefly"
   - "What are the main points?"
   - "Give me a quick overview"
   - → Use: `search_documents_tool` or `summarize_document_tool`

3. **Information Lookup**
   - "Find information about X"
   - "What does the document say about..."
   - "I need facts about..."
   - → Use: `search_documents_tool`

4. **Explanation of Concepts**
   - "Explain how X works based on the documents"
   - "What is Y according to these sources?"
   - → Use: `search_documents_tool`

### Use `deep_research_tool` when:

The user is asking for:

1. **Comparisons Across Documents**
   - "Compare the perspectives on gold in these documents"
   - "How do different sources view this issue?"
   - "What are the differences between..."
   - → Use: `deep_research_tool`

2. **Analysis and Review**
   - "Analyze the gold market"
   - "Review the evidence on this topic"
   - "What can we conclude from..."
   - → Use: `deep_research_tool`

3. **Contradiction Detection**
   - "Are there contradictions in these sources?"
   - "Where do documents disagree?"
   - "What conflicts exist between..."
   - → Use: `deep_research_tool`

4. **Trend and Pattern Recognition**
   - "What trends do you see?"
   - "Identify patterns in this evidence"
   - "What themes emerge?"
   - → Use: `deep_research_tool`

5. **Risk and Opportunity Assessment**
   - "What are the risks?"
   - "What opportunities exist?"
   - "What could go wrong or right?"
   - → Use: `deep_research_tool`

6. **Executive Summaries and Strategic Reports**
   - "Create an executive summary"
   - "Write a comprehensive report"
   - "Provide strategic implications"
   - → Use: `deep_research_tool`

7. **Comprehensive Research**
   - "Conduct deep research on..."
   - "I need a thorough analysis"
   - "Research this comprehensively"
   - → Use: `deep_research_tool`

8. **Confidence and Uncertainty Assessment**
   - "How confident are we about...?"
   - "What's the evidence for...?"
   - "How well-supported is this claim?"
   - → Use: `deep_research_tool` (provides broader context)

## Keyword Recognition for Tool Selection

### Keywords suggesting `search_documents_tool`:

- What is...?
- Who...?
- When...?
- Where...?
- Find...
- Look up...
- Define...
- Explain...
- What does the document say about...?
- Brief summary
- Quick answer
- List...

### Keywords suggesting `deep_research_tool`:

- Compare
- Contrast
- Analyze
- Review
- Examine
- Investigate
- Research
- Trend
- Pattern
- Contradiction
- Disagreement
- Agreement
- Risk
- Opportunity
- Executive summary
- Comprehensive
- Strategic
- Synthesis
- Evidence-based conclusion
- How confident are you...?
- What's the relationship between...?

## Multi-Step Retrieval Strategies

### Strategy 1: Quick Answer Then Deep Dive

**Situation**: User asks for quick answer that might benefit from deeper analysis

**Process**:
1. Use `search_documents_tool` for initial quick answer
2. If user seems to want more depth, follow up with `deep_research_tool`

**Example**:
```
User: "What's the gold price outlook?"
Step 1: Use search_documents_tool → Get quick factual answer
Step 2: Follow up: "Would you like a deeper analysis?" → Use deep_research_tool if yes
```

### Strategy 2: Deep Research First, Then Targeted Queries

**Situation**: Complex topic requiring comprehensive understanding, then specific details

**Process**:
1. Use `deep_research_tool` to establish overall understanding
2. Use `search_documents_tool` for specific factual questions that emerge

**Example**:
```
User: "Comprehensive analysis of gold market risks"
Step 1: Use deep_research_tool → Get comprehensive analysis
Step 2: If user asks "But what's the specific production forecast?" → Use search_documents_tool
```

### Strategy 3: Comparative Analysis

**Situation**: User wants to compare perspectives or trends

**Process**:
1. Always use `deep_research_tool` with comparative query
2. Let the tool structure evidence for cross-document analysis

**Example**:
```
User: "How do mining companies view gold differently than investors?"
Step 1: Use deep_research_tool with query focused on comparison
```

## Tool Configuration and Parameters

### When using `search_documents_tool`:

- **Purpose**: Quick retrieval of specific information
- **Top K**: 8 chunks (default, sufficient for factual questions)
- **Expected Output**: Clean evidence with source attribution
- **Time**: Fast response

### When using `deep_research_tool`:

- **Purpose**: Comprehensive multi-document analysis
- **Top K**: 40 chunks (default, comprehensive coverage)
- **Expected Output**: Structured evidence organized by document
- **Features**: Deduplication, chunk grouping (max 5 per document)
- **Output Format**: Organized by document with key evidence sections
- **Includes**: Boilerplate filtering and text cleaning
- **Time**: May take longer due to comprehensive retrieval and processing

## Reasoning Rules for Tool Selection

1. **Start with user intent**: What is the user really trying to accomplish?

2. **Count information sources**: 
   - Quick lookup of 1-2 facts → `search_documents_tool`
   - Synthesis across multiple documents → `deep_research_tool`

3. **Assess question complexity**:
   - Simple factual → `search_documents_tool`
   - Complex analytical → `deep_research_tool`

4. **Check for synthesis requirement**:
   - "Find X" → `search_documents_tool`
   - "Compare X and Y" → `deep_research_tool`
   - "Synthesize viewpoints on X" → `deep_research_tool`

5. **Evaluate evidence needs**:
   - Limited evidence sufficient → `search_documents_tool`
   - Comprehensive evidence needed → `deep_research_tool`

## Error Recovery

If initial tool choice seems wrong:

- **Initial choice was `search_documents_tool` but result too shallow**:
  - Follow up with: "Let me conduct deeper research..." → Use `deep_research_tool`

- **Initial choice was `deep_research_tool` but user wants quick answer**:
  - Extract key factual answers from deep research results
  - Or follow up with: "For specific facts..." → Use `search_documents_tool`

## Best Practices

1. **Tool Selection Should Be Transparent**: Consider mentioning to the user why you're using a particular tool

2. **Combine Tools Strategically**: Don't limit yourself to one tool; use both as needed

3. **Learn from Context**: If you've already retrieved evidence with one tool, consider whether you have enough information to answer without another tool

4. **Respect User Preferences**: If a user indicates they want quick answers, use `search_documents_tool`; if they want depth, use `deep_research_tool`

5. **Optimize for Time and Cost**: `search_documents_tool` is faster; use it when sufficient for the user's needs

## Decision Tree

```
User asks a question

→ Is it a straightforward factual lookup?
  YES → use search_documents_tool
  NO → continue

→ Does the user explicitly ask for analysis, comparison, or comprehensive research?
  YES → use deep_research_tool
  NO → continue

→ Does the answer require synthesizing multiple documents?
  YES → use deep_research_tool
  NO → use search_documents_tool

→ If uncertain, ask the user: "Would you like a quick summary or a deeper analysis?"
```
