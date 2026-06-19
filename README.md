# Adaptive Domain-Aware RAG Platform

> A full-stack intelligent document research system with adaptive semantic domains, hybrid embeddings, automated news ingestion, and a Deep Agent that can use skills, tools, and long-term research memory.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?style=flat-square&logo=elasticsearch)](https://www.elastic.co)
[![DeepAgents](https://img.shields.io/badge/DeepAgents-Agent_Framework-blue?style=flat-square)](https://github.com/langchain-ai/deepagents)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT_&_Embeddings-412991?style=flat-square&logo=openai)](https://openai.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Modal](https://img.shields.io/badge/Modal-1.5.0+-7C3AED?style=flat-square)](https://modal.com)

---

# Overview

This project is an adaptive Retrieval-Augmented Generation (RAG) platform for document and news-based research. It combines:

- Document ingestion and text extraction
- LLM-powered metadata extraction
- Hybrid semantic embeddings
- Elasticsearch vector retrieval
- Adaptive domain assignment through learned centroids
- A Deep Agent for multi-step research and reasoning
- Skill-guided tool selection
- Long-term research memory for important findings

Instead of treating the assistant as a simple one-shot RAG chatbot, the current system uses a Deep Agent that can plan, choose specialized tools, analyze evidence from different angles, synthesize findings, and store useful research summaries for later context.

---

# New CLI Functions

The project now includes three convenient command‑line utilities:

- **Sandbox mode** – `python -m backend.sandbox run <script>`
  Executes Python scripts in an isolated virtual environment with limited filesystem access, preventing side‑effects on the host system.

- **Modal integration** – `modal deploy` / `modal run <function>`
  Deploys heavy‑weight background jobs (e.g., embedding generation, large retrieval tasks) to Modal’s serverless platform directly from the repo.

- **Office CLI** – `office-cli <command>`
  Provides quick access to common administrative tasks:
  - `office-cli start` – launches the FastAPI backend and React frontend together.
  - `office-cli stop` – stops all Docker containers.
  - `office-cli restart` – restarts the development environment.
  - `office-cli logs` – streams logs from the backend, frontend, and Elasticsearch services.

These tools streamline development, testing, and production workflows while keeping the local environment clean.


# Key Features

## Intelligent Document Ingestion

Supported formats:

- PDF
- DOCX
- TXT
- Markdown

Ingestion flow:

```text
Upload
  -> Text extraction
  -> Metadata extraction
  -> Chunking
  -> Hybrid embedding generation
  -> Elasticsearch indexing
  -> Adaptive domain assignment
  -> Domain centroid update
```

The metadata extraction pipeline identifies titles, keywords, entities, regions, publication details, and contextual summaries. These fields improve retrieval precision and domain classification.

## Automated News Ingestion

The backend integrates Tavily for external news retrieval. News articles are fetched, extracted, saved as text, embedded, indexed, and assigned to domains using the same semantic pipeline as uploaded documents.

This allows the knowledge base to expand from both user-uploaded files and fresh external sources.

## Hybrid Embedding Architecture

The platform combines metadata meaning with document content meaning:

```python
hybrid_embedding = (metadata_embedding * 0.7) + (chunk_centroid_embedding * 0.3)
```

This gives each document a richer semantic representation than content-only chunk embeddings. The hybrid embedding is used for classification, retrieval, and domain centroid updates.

## Adaptive Domain Centroids

Domains are adaptive semantic entities rather than static folders.

Each domain starts with an embedding from its name and description. As documents are assigned, the domain centroid is recomputed from the assigned documents:

```python
domain_centroid = average(all_hybrid_embeddings_in_domain)
```

This lets domains learn from the content they contain. Empty domains fall back to their original name/description embedding, while populated domains evolve around the actual documents assigned to them.

---

# Deep Agent Architecture

The current query system uses `deepagents.create_deep_agent` through `backend/app/services/rag_agent_service.py`.

The Deep Agent is designed for multi-step analytical research. It can:

- Retrieve direct evidence
- Summarize relevant documents
- Compare perspectives across documents
- Identify trends and recurring themes
- Assess risks, contradictions, uncertainty, and confidence
- Synthesize evidence into executive-level conclusions
- Save important research findings into memory

The `/query` endpoint creates the Deep Agent for every user query and scopes retrieval based on the frontend request:

- `global`: search across the whole indexed knowledge base
- `folders`: resolve selected domain/folder IDs into document IDs
- `documents`: search only selected documents
- legacy `document_id`: fallback support for older single-document calls

## Deep Agent Skills

The agent is configured with three local skill files:

| Skill | File | Purpose |
|------|------|---------|
| Retrieval Strategy | `backend/app/skills/retrieval_strategy.md` | Teaches the agent when to use quick search versus deep research and how to combine tools. |
| Analytical Review | `backend/app/skills/analytical_review.md` | Guides structured, evidence-based analysis across documents. |
| Comparative Analysis | `backend/app/skills/comparative_analysis.md` | Helps compare viewpoints, agreements, disagreements, and source perspectives. |

These skills act as reusable reasoning instructions. They help the Deep Agent decide which tools to call, when to plan, and how to structure analytical answers.

## Deep Agent Tools

The agent currently has six specialized tools:

| Tool | Purpose |
|------|---------|
| `search_documents_tool` | Fast Elasticsearch retrieval for factual questions, lookups, and direct evidence. |
| `summarize_document_tool` | Summarizes relevant retrieved content for overviews and document summaries. |
| `compare_documents_tool` | Compares documents, viewpoints, forecasts, agreements, disagreements, and unique perspectives. |
| `identify_trends_tool` | Finds recurring themes, patterns, emerging signals, and trend evidence across documents. |
| `risk_analysis_tool` | Identifies risks, uncertainty, contradictions, evidence gaps, and confidence signals. |
| `deep_research_tool` | Synthesizes evidence into executive-level conclusions, implications, opportunities, and recommendations. |

For simple factual questions, the agent can call `search_documents_tool` directly. For complex questions, it can use several tools in sequence before producing a final synthesis.

## Deep Agent Memory

The agent is connected to long-term research memory:

```text
backend/app/memory/research_history.md
```

After a query finishes, `backend/app/services/memory_service.py` evaluates whether the answer deserves long-term storage. It saves only important research outputs such as:

- Strategic analysis
- Trends
- Comparisons
- Risks
- Investment insights
- Executive conclusions
- Important findings that may be useful later

Simple lookups, short Q&A, trivial summaries, and navigation-style questions are skipped.

When memory is saved, it is compacted into a short entry containing the topic, key findings, risks, confidence level, and final conclusion. Docker Compose mounts `backend/app/memory` as a persistent volume path so research history survives backend container restarts.

## Query Reasoning Flow

```text
User query
  -> Frontend sends scope and query to /query
  -> Backend creates scoped Deep Agent
  -> Agent reads skills and memory
  -> Agent selects tools based on intent
  -> Retrieval tools query Elasticsearch
  -> Specialized tools analyze evidence
  -> Deep research tool synthesizes findings when needed
  -> Final answer is returned with source-grounded reasoning
  -> Important research outputs are saved to memory
```

The agent is instructed to base conclusions only on retrieved evidence, cite sources explicitly, acknowledge uncertainty, and avoid speculation beyond the documents.

---

# Retrieval And Evidence Grounding

Retrieval is powered by Elasticsearch and OpenAI embeddings. User queries are embedded, matched against indexed document chunks, and filtered by the selected query scope.

Evidence is cleaned and grouped before analysis:

- Duplicate chunks are removed
- Boilerplate text is filtered
- Results are grouped by document
- Top chunks per document are retained
- Source document names are preserved for attribution

Every analytical answer is expected to include source attribution, confidence notes, and limitations when evidence is incomplete.

---

# Frontend Features

The frontend is built with React and Vite.

Current UI capabilities include:

- AI chat interface
- Global, folder/domain, and document-scoped querying
- Domain/folder navigation
- Document upload modal
- Metadata editor
- Markdown response rendering
- Multi-document querying
- Document repository management
- Latest gold news ingestion trigger

---

# System Architecture

```text
Frontend: React + Vite
  -> Chat UI
  -> Upload and metadata modals
  -> Domain/folder navigation
  -> Document repository

Backend: FastAPI
  -> Routers for ingestion, query, news, and documents
  -> Deep Agent service
  -> Retrieval service
  -> Memory service
  -> Metadata and extraction services
  -> Domain assignment and centroid services
  -> Elasticsearch vector service

Storage:
  -> SQLite metadata database
  -> Elasticsearch dense vector index
  -> Uploaded files and downloaded news articles
  -> Research memory Markdown file

External APIs:
  -> OpenAI for LLM and embeddings
  -> Tavily for news retrieval
```

---

# Tech Stack

## Frontend

| Layer | Technology |
|------|------------|
| Framework | React 19 |
| Build Tool | Vite 8 |
| Styling | TailwindCSS |
| Rendering | Markdown renderer |

## Backend

| Layer | Technology |
|------|------------|
| Framework | FastAPI |
| Database | SQLite |
| Vector DB | Elasticsearch 8.x |
| Agent Framework | DeepAgents + LangChain |
| Embeddings | OpenAI embeddings |
| LLM | `gpt-5.4-nano` |
| News Retrieval | Tavily API |
| Document Parsing | `pypdf`, `python-docx` |
| Scheduling | APScheduler |
| Vector Operations | NumPy / vector math through services |

---

# Project Structure

```text
Internproject2/
|-- backend/
|   |-- app/
|   |   |-- core/
|   |   |   |-- config.py
|   |   |   `-- paths.py
|   |   |-- db/
|   |   |   |-- database.py
|   |   |   `-- documents.db
|   |   |-- memory/
|   |   |   |-- research_history.md
|   |   |   `-- research_history_template.md
|   |   |-- prompts/
|   |   |   |-- domain_assignment_prompt.py
|   |   |   `-- metadata_prompt.py
|   |   |-- routers/
|   |   |   |-- documents.py
|   |   |   |-- ingest.py
|   |   |   |-- news.py
|   |   |   `-- query.py
|   |   |-- services/
|   |   |   |-- document_ingestion_service.py
|   |   |   |-- document_service.py
|   |   |   |-- domain_assignment_service.py
|   |   |   |-- domain_centroid_service.py
|   |   |   |-- domain_service.py
|   |   |   |-- domain_similarity_service.py
|   |   |   |-- extraction_service.py
|   |   |   |-- file_service.py
|   |   |   |-- hybrid_embedding_service.py
|   |   |   |-- memory_service.py
|   |   |   |-- metadata_extraction_service.py
|   |   |   |-- metadata_service.py
|   |   |   |-- news_ingestion_service.py
|   |   |   |-- rag_agent_service.py
|   |   |   |-- retrieval_service.py
|   |   |   |-- scheduler_service.py
|   |   |   |-- text_extraction_service.py
|   |   |   `-- vector_service.py
|   |   `-- skills/
|   |       |-- analytical_review.md
|   |       |-- comparative_analysis.md
|   |       `-- retrieval_strategy.md
|   |-- storage/
|   |   |-- news_articles/
|   |   |-- outputs/
|   |   `-- uploads/
|   |-- main.py
|   |-- pyproject.toml
|   |-- uv.lock
|   `-- Dockerfile
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |-- pages/
|   |   |-- services/
|   |   |-- App.jsx
|   |   |-- main.jsx
|   |   |-- index.css
|   |   `-- App.css
|   |-- public/
|   |-- package.json
|   |-- vite.config.js
|   `-- Dockerfile
`-- docker-compose.yml
```

---

# Detailed System Flow

## Ingestion Phase

```text
User uploads document or news article is fetched
  -> Text extraction converts source to raw text
  -> Metadata extraction identifies semantic context
  -> Chunking splits document into searchable pieces
  -> Hybrid embedding service creates document-level representation
  -> Elasticsearch indexes chunks and vectors
  -> Domain similarity service compares against adaptive centroids
  -> Document is assigned to best matching domain
  -> Domain centroid is recomputed
```

## Retrieval Phase

```text
User submits query through chat
  -> Frontend sends query and retrieval scope
  -> Backend creates scoped Deep Agent
  -> Retrieval tool embeds the query
  -> Elasticsearch returns relevant chunks
  -> Results are cleaned, deduplicated, grouped, and ranked
```

## Reasoning Phase

```text
Deep Agent receives user request
  -> Reads skill instructions and memory
  -> Selects the right tool or tool sequence
  -> Retrieves and analyzes evidence
  -> Compares, identifies trends, or assesses risks when needed
  -> Synthesizes final answer
  -> Stores important research memory when appropriate
```

---

# Deployment And Setup

## Prerequisites

- Python 3.11+
- Node.js 18+
- Elasticsearch 8.x
- OpenAI API key
- Tavily API key for news ingestion

## Environment Configuration

Create `backend/.env`:

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
ELASTICSEARCH_URL=http://localhost:9200
DATABASE_URL=sqlite:///./knowledge_base.db
```

Create `frontend/.env.docker` if using Docker and the frontend needs a backend API URL for your environment.

## Docker Compose

```bash
docker-compose up
```

This starts:

- Elasticsearch on port `9200`
- FastAPI backend on port `8000`
- React frontend on port `5173`

## Manual Backend Setup

Recommended with `uv`:

```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Alternative with `pip`:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e .
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Manual Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

# API Highlights

| Endpoint | Method | Purpose |
|---------|--------|---------|
| `/query` | POST | Run a scoped Deep Agent query across global, folder, or document context. |
| `/field-search` | POST | Extract requested fields from a document using the Deep Agent and retrieval tools. |
| `/test-news` | GET | Test Tavily news retrieval. |
| `/test-extract` | GET | Test article extraction. |
| `/test-save-news` | GET | Test saving extracted news as text. |

Example `/query` request:

```json
{
  "query": "Compare the main risks discussed across these gold market documents.",
  "scope_type": "documents",
  "document_ids": ["doc_1", "doc_2"]
}
```

---

# Roadmap

Planned or natural next improvements:

- Streaming responses in the chat UI
- Redis caching for repeated retrieval and agent outputs
- Stronger source citation formatting in frontend responses
- Authentication and role-based access control
- Analytics dashboard for query trends and domain health
- Knowledge graph view for entities and relationships
- Scheduled news ingestion jobs
- Expanded memory management UI
- Multi-agent workflows for specialized research modes

---

# Project Summary

This project demonstrates a modern full-stack AI research system:

1. Adaptive domains learn from assigned documents.
2. Hybrid embeddings combine metadata and content signals.
3. Elasticsearch powers scoped semantic retrieval.
4. A Deep Agent uses skills and specialized tools for multi-step analysis.
5. Research memory stores important findings for future context.
6. The frontend exposes practical workflows for upload, search, chat, and repository management.

The result is more than a static document chatbot. It is a growing research workspace that can retrieve, reason, synthesize, and remember.
