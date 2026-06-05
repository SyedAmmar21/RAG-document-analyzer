# Analytical Review Skill

## Purpose

Guide the Deep Agent to perform structured, evidence-based analysis across multiple documents.

This skill teaches the agent to:
- Synthesize information across documents
- Compare and contrast viewpoints
- Identify areas of agreement and disagreement
- Detect contradictions and tensions
- Recognize recurring themes and patterns
- Identify emerging risks and opportunities
- Assess uncertainty and confidence levels
- Generate executive summaries

## When to Use This Skill

Apply this analysis framework when the user asks for:
- Comparisons between documents
- Comprehensive analysis
- Trend identification
- Contradiction detection
- Strategic reviews
- Risk assessments
- Opportunity identification
- Executive summaries
- In-depth research

## Analysis Process

Follow this structured process for comprehensive analysis:

### 1. Review All Evidence

- Read through ALL retrieved evidence chunks
- Note the source document for each piece of evidence
- Identify the context and scope of each source

### 2. Map Key Points by Document

For each document, identify:
- Central thesis or main message
- Supporting evidence and examples
- Methodology or data sources cited
- Confidence level of claims
- Caveats or limitations mentioned

### 3. Cross-Document Comparison

Systematically compare documents across dimensions:

**Areas of Agreement:**
- What points are consistently mentioned across multiple documents?
- Where do documents reinforce each other?
- What is the strongest consensus?

**Areas of Disagreement:**
- Where do documents contradict each other?
- What different interpretations exist?
- Are there data conflicts?
- Do documents prioritize different aspects?

**Complementary Information:**
- What unique information does each document provide?
- How do different sources fill gaps in understanding?
- What emerges only when combining sources?

### 4. Pattern Recognition

Identify:
- **Recurring Themes**: Concepts mentioned across multiple documents
- **Emerging Patterns**: Trends or progressions indicated by the evidence
- **Underlying Causes**: Root factors mentioned or implied across sources
- **Consequences**: Downstream effects discussed in the evidence
- **Connections**: Relationships between ideas across documents

### 5. Risk and Opportunity Assessment

From the evidence, extract:

**Risks:**
- What potential negative outcomes are discussed?
- What vulnerabilities are mentioned?
- What uncertainties could impact outcomes?
- What contradictions create confusion or risk?

**Opportunities:**
- What positive possibilities are indicated?
- What gaps could be addressed?
- What emerging trends could be leveraged?
- What areas show growth potential?

### 6. Uncertainty and Confidence Assessment

For each conclusion, evaluate:

**Confidence Levels:**
- **High**: Multiple sources agree; supported by data or specific examples
- **Moderate**: Some sources support the point; reasonable inference from evidence
- **Low**: Limited evidence; inferential or speculative; significant uncertainty
- **Conflicted**: Evidence contradicts on this point; no clear consensus

**Express Uncertainty Explicitly:**
- "Based on available evidence, X appears true, but we should note..."
- "While documents suggest Y, there is some disagreement on..."
- "This conclusion is moderately supported by..."
- "We cannot fully determine Z from the retrieved evidence because..."

### 7. Structured Output

Organize findings into clear sections:

## Output Template

Use this structure for your analysis:

### Executive Summary

- 2-3 sentence overview of key findings
- Primary conclusion or recommendation
- High-level confidence assessment

### Key Findings

- 3-5 most important discoveries
- Each finding supported by evidence from specific sources
- Clear statement of what the evidence shows

### Areas of Agreement

- Points consistently supported across documents
- Why this consensus matters
- Strength of agreement (unanimous, majority, etc.)

### Areas of Disagreement

- Specific contradictions or differing viewpoints
- Reasons for the disagreement (different data, different priorities, different analysis)
- Which documents take which positions
- Whether disagreement is substantive or terminological

### Risks

- Specific risks identified in the evidence
- Likelihood assessment
- Potential impact
- Mitigation strategies mentioned (if any)
- Confidence in risk assessment

### Opportunities

- Specific opportunities identified
- Potential benefits
- Feasibility assessment
- Enabling conditions (what would need to happen)
- Supporting evidence

### Supporting Evidence

For each major claim above, provide:
- Direct quotes or specific references from sources
- Document names and context
- Why this evidence is compelling

Example format:
> "This finding is supported by [Document A] which states: '[quote]', and confirmed by [Document B] which shows: '[quote]'."

### Confidence Assessment

- Overall confidence in the analysis
- Areas of high confidence and why
- Areas of uncertainty or limited evidence
- Gaps in the retrieved information
- Recommendations for additional research

## Key Principles

1. **Evidence-Based**: Every claim must be supported by retrieved documents. Do not speculate beyond the evidence.

2. **Source Attribution**: Always cite which documents support each point. Use clear attribution like [Document Name].

3. **Structured Reasoning**: Use explicit logical connectors:
   - "This suggests that..."
   - "As a result..."
   - "In contrast..."
   - "This implies..."
   - "The evidence indicates..."

4. **Comparative Thinking**: Actively compare rather than merely summarize. Show relationships between documents.

5. **Intellectual Honesty**: Acknowledge:
   - Conflicting evidence
   - Areas of uncertainty
   - Limitations of the analysis
   - Gaps in information

6. **Avoid Isolated Summaries**: Don't just summarize each document separately. Synthesize across them.

7. **Avoid Hallucination**: Restrict conclusions to what the evidence supports. If evidence is limited, say so explicitly.

## Example Analysis Framework

For a query like "Compare gold market outlook across recent sources":

1. **Map viewpoints**: What does each source say about gold prices, demand, risks?
2. **Find agreements**: Do sources agree on any outlook elements?
3. **Find disagreements**: Where do outlooks diverge?
4. **Identify patterns**: What themes appear across multiple sources?
5. **Assess uncertainty**: Which predictions are well-supported vs. speculative?
6. **Structure output**: Use the template above to organize findings

## Tips for Better Analysis

- **Look for implicit information**: Don't just extract explicit statements; identify implications and connections
- **Note qualifiers**: When sources say "may," "could," "appears," or "suggests," these indicate uncertainty
- **Check methodology**: When sources cite data, assess whether data sources and methodologies are comparable
- **Identify author perspective**: Different sources may have inherent biases; note these
- **Build understanding incrementally**: Start with agreements, then explore disagreements, then assess confidence

## When You Have Limited Evidence

If retrieved evidence is sparse:
- Explicitly state that evidence is limited
- Provide analysis on what is available
- Recommend additional retrieval or research
- Focus on high-confidence findings only
- Acknowledge speculative elements clearly
