# Adaptive Domain-Aware RAG Platform

Full-stack research workspace for gold-market documents and news. The app ingests files, extracts metadata, indexes chunks into Elasticsearch, assigns each document into semantic folders, and answers scoped questions through a Deep Agent with Redis-backed memory and optional sandbox tooling.

## What the project does

This repository combines:

- A React + Vite frontend for chat, document management, metadata review, and semantic folders
- A FastAPI backend for ingestion, retrieval, news ingestion, and agent orchestration
- Elasticsearch for chunk-level vector retrieval
- SQLite for document, metadata, and domain records
- Redis for searchable research memory used by the agent
- Tavily + Trafilatura for fetching and extracting fresh news articles
- Modal or Cube-based sandbox support for isolated document-generation workflows when sandbox mode is enabled

The current UI and backend are tailored around a gold research workflow, but the architecture is general RAG infrastructure with domain-aware organization.

## Core features

### 1. Document upload and ingestion

Supported upload types:

- PDF
- DOCX
- TXT

When a file is uploaded to /ingest, the backend:

1. validates size and extension
2. checks for duplicates by original upload name
3. saves the file under backend/storage/uploads
4. extracts raw text
5. extracts metadata
6. chunks and embeds the text
7. indexes chunks into Elasticsearch
8. generates a document-level hybrid embedding
9. assigns the document into the best semantic folder/domain

Key files:

- [backend/app/routers/ingest.py](backend/app/routers/ingest.py)
- [backend/app/services/document_ingestion_service.py](backend/app/services/document_ingestion_service.py)
- [backend/app/services/file_service.py](backend/app/services/file_service.py)
- [backend/app/services/text_extraction_service.py](backend/app/services/text_extraction_service.py)

### 2. Metadata extraction

Metadata extraction is a hybrid of rule-based parsing and LLM extraction.

Fields currently used:

- title
- published_date
- focus
- entities
- economic_indicators
- regions

How it works:

- published_date, entity mentions, regions, and economic indicators are first detected with regex/rule-based logic
- ChatOpenAI is then used to infer higher-level semantic metadata such as title/focus and enrich the lists
- the merged metadata is stored in SQLite and shown in the frontend metadata review modal

Key file:

- [backend/app/services/metadata_extraction_service.py](backend/app/services/metadata_extraction_service.py)

### 3. Hybrid embeddings

The app does not rely only on raw chunk embeddings. It builds a document-level hybrid embedding:

- 70% metadata embedding
- 30% centroid of top document chunks

That hybrid vector is then used for semantic domain assignment.

Key files:

- [backend/app/services/hybrid_embedding_service.py](backend/app/services/hybrid_embedding_service.py)
- [backend/app/services/document_centroid_service.py](backend/app/services/document_centroid_service.py)

### 4. Elasticsearch vector retrieval

All searchable document chunks are stored in the documents Elasticsearch index as:

- document_id
- text
- embedding

Queries are embedded with text-embedding-3-small, then executed as Elasticsearch knn search. Query scope can be:

- global
- selected folders
- selected documents
- legacy single-document mode

Key files:

- [backend/app/services/vector_service.py](backend/app/services/vector_service.py)
- [backend/app/services/retrieval_service.py](backend/app/services/retrieval_service.py)

### 5. Semantic folders / adaptive domains

Folders in the UI are backed by semantic domains in SQLite, not static filesystem folders.

What happens:

- a domain is created with a name + optional description
- that text is embedded immediately
- new documents are matched against stored domain embeddings with cosine similarity
- once documents are assigned, the domain centroid is recomputed from its assigned documents

This makes folder assignment semantic rather than manual-only. There is also a synthetic fallback folder called Unorganized Files for documents with no current domain assignment.

Key files:

- [backend/app/services/domain_service.py](backend/app/services/domain_service.py)
- [backend/app/services/domain_similarity_service.py](backend/app/services/domain_similarity_service.py)
- [backend/app/services/domain_centroid_service.py](backend/app/services/domain_centroid_service.py)
- [backend/app/services/domain_assignment_service.py](backend/app/services/domain_assignment_service.py)

### 6. Deep Agent for question answering

The /query route creates a Deep Agent that can answer questions over the selected workspace scope.

Agent behavior in this repo:

- quick retrieval with search_documents_tool
- summarization
- comparison across documents
- trend detection
- risk analysis
- executive synthesis
- retrieval of prior research memories from Redis
- optional sandbox execution for OfficeCLI workflows

The main agent model in the current code is AWS Bedrock Claude Haiku via ChatBedrockConverse, while some supporting services still use OpenAI models for metadata extraction, memory scoring, and embeddings.

Key files:

- [backend/app/routers/query.py](backend/app/routers/query.py)
- [backend/app/services/rag_agent_service.py](backend/app/services/rag_agent_service.py)
- [backend/app/skills](backend/app/skills)

### 7. Redis-backed long-term research memory

Redis is actively used in this project.

What it stores:

- compact summaries of high-value research outputs
- the original user query
- timestamped memory items under the memories namespace

How it is used:

- after a query, memory_service.py decides whether the answer is important enough to save
- if yes, the answer is summarized and written to backend/app/memory/research_history.md
- the same summary is also saved into Redis through RedisStore
- when a user asks about previous findings, earlier research, memory, or prior conclusions, the backend preloads matching Redis memories into the agent context

Redis is also mounted in Docker via redis/redis-stack, which gives both the Redis server and Redis Stack capabilities.

Key files:

- [backend/app/services/redis_store_service.py](backend/app/services/redis_store_service.py)
- [backend/app/services/memory_service.py](backend/app/services/memory_service.py)

### 8. Tavily-powered latest news ingestion

Tavily is one of the main live features in this codebase.

The news ingestion flow:

1. run several focused gold-market search queries through Tavily
2. deduplicate articles by canonicalized URL and normalized title
3. extract article text with Trafilatura
4. fall back to Tavily Extract if needed
5. save the article as a text file under backend/storage/news_articles
6. run the exact same ingestion pipeline used for uploaded documents
7. assign the article into a semantic domain
8. return processed / skipped / failed results to the frontend

The frontend exposes this with the Download Latest Gold News button and summary modals.

Key files:

- [backend/app/routers/news.py](backend/app/routers/news.py)
- [backend/app/services/news_ingestion_service.py](backend/app/services/news_ingestion_service.py)

### 9. Scheduled ingestion with APScheduler

News ingestion is not only manual. The backend starts an APScheduler background scheduler on app startup.

Current scheduled behavior:

- daily gold news ingestion
- runs at 10:00 AM Asia/Kuala_Lumpur
- stores the most recent run summary in memory
- frontend polls /news/scheduled-summary every 30 seconds and shows the result once

Key files:

- [backend/main.py](backend/main.py)
- [backend/app/services/scheduler_service.py](backend/app/services/scheduler_service.py)

### 10. Sandbox execution and OfficeCLI

The project includes an optional isolated sandbox path for document generation and command execution.

What is implemented today:

- a ModalSandboxService and Cube-backed sandbox service that create and terminate sandboxes
- thread-scoped sandbox reuse, so one chat thread can keep working inside the same sandbox session
- cleanup of idle sandbox sessions
- agent tool access through sandbox_execute
- tracking of generated files and downloading them back into backend/storage/outputs
- current-working-document tracking for follow-up edits

The sandbox abstraction is provider-agnostic, so the agent uses the same tool interface whether the backend is Cube or Modal.

Current provider behavior:

- Cube sandbox is the current default provider in this repository and is configured through the Cube/E2B settings in backend environment variables
- Modal sandbox is supported as an alternative and can be enabled by switching the provider configuration

To switch from Cube to Modal, update the environment variables to:

- set SANDBOX_PROVIDER=modal
- enable USE_MODAL_SANDBOX=true
- provide MODAL_APP_NAME and the required Modal credentials

When the sandbox is enabled, the agent can run OfficeCLI-oriented commands inside the sandbox to generate or modify:

- pptx
- docx
- xlsx
- pdf

There is also a legacy backend export path through OfficeDocumentService and sandbox_service.py for generated files.

Key files:

- [backend/app/services/modal_sandbox_service.py](backend/app/services/modal_sandbox_service.py)
- [backend/app/services/sandbox/session_store.py](backend/app/services/sandbox/session_store.py)
- [backend/app/services/office_document_service.py](backend/app/services/office_document_service.py)
- [backend/app/services/sandbox_service.py](backend/app/services/sandbox_service.py)
- [backend/app/services/sandbox/cube](backend/app/services/sandbox/cube)
- [backend/app/services/sandbox/modal](backend/app/services/sandbox/modal)

## Frontend features

The frontend is a React workspace with three main tabs:

- Main: chat, scope selection, upload flow, latest news download
- Repository: searchable document table with open, metadata, use, and delete actions
- Folders: create/edit/delete semantic folders and inspect the documents inside them

Notable frontend behaviors:

- each chat session gets a stable thread_id via crypto.randomUUID()
- users can scope retrieval to selected folders or selected documents
- duplicate uploads show a dedicated duplicate alert
- metadata suggestions and domain suggestions are reviewed in a modal after ingestion
- scheduled news ingestion results are automatically surfaced through polling

Key files:

- [frontend/src/pages/Home.jsx](frontend/src/pages/Home.jsx)
- [frontend/src/components/ChatWindow.jsx](frontend/src/components/ChatWindow.jsx)
- [frontend/src/components/DocumentRepository.jsx](frontend/src/components/DocumentRepository.jsx)
- [frontend/src/components/SidebarFolders.jsx](frontend/src/components/SidebarFolders.jsx)
- [frontend/src/components/FoldersView.jsx](frontend/src/components/FoldersView.jsx)

## API routes in use

Current main routes:

- POST /ingest - upload and ingest a file
- POST /reindex - re-run ingestion across saved documents
- POST /query - run the Deep Agent over the selected scope
- POST /news/ingest-latest - fetch and ingest the latest gold news
- GET /news/scheduled-summary - fetch the latest scheduled-ingestion result
- GET /documents - list repository documents
- DELETE /documents/{document_id} - delete a document and its Elasticsearch chunks
- GET /documents/{document_id}/view - open the stored source file
- GET /documents/{document_id}/metadata - get metadata + domain
- POST /documents/{document_id}/metadata - save metadata/domain for a specific document
- POST /metadata/save - save metadata/domain through the modal workflow
- GET /domains - list semantic folders/domains
- POST /domains - create a domain
- PUT /domains/{domain_id} - update a domain
- DELETE /domains/{domain_id} - delete a domain
- GET /domains/{domain_id}/documents - list documents inside a domain
- POST /generate-presentation - legacy presentation export route

## Storage layout

Main storage paths:

- backend/storage/uploads - uploaded source files
- backend/storage/news_articles - saved Tavily/trafilatura article text files
- backend/storage/outputs - generated sandbox/export outputs
- backend/app/db/documents.db - SQLite database
- backend/app/memory/research_history.md - append-only saved research memory log

app/core/paths.py centralizes storage path handling and includes relative-path safety checks to prevent escaping the storage root.

## Tech stack

### Frontend

- React 19
- Vite 8
- plain CSS with app-specific workspace components

### Backend

- FastAPI
- Elasticsearch 8
- SQLite
- Redis / Redis Stack
- DeepAgents
- LangChain
- LangGraph
- APScheduler
- Modal
- Tavily
- Trafilatura
- pypdf
- python-docx

### Model usage in the current code

- OpenAI text-embedding-3-small for embeddings
- OpenAI gpt-5.4-nano for metadata extraction and memory evaluation/summarization
- AWS Bedrock Claude Haiku for the main Deep Agent response path

## Running locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop if using docker-compose
- API access for the services you want enabled

### Backend environment

Create backend/.env with the variables your setup needs:

```env
OPENAI_API_KEY=...
ELASTICSEARCH_HOST=http://elasticsearch:9200
TAVILY_API_KEY=...
REDIS_URL=redis://rag-redis:6379
AWS_REGION=...
MAX_FILE_SIZE=5242880

# Sandbox selection
SANDBOX_PROVIDER=cube
USE_MODAL_SANDBOX=true
MODAL_APP_NAME=rag-document-analyzer

# Cube settings
CUBE_REMOTE_PROXY_BASE=https://your-cube-host:443
E2B_API_URL=http://your-cube-host:3000
E2B_API_KEY=your-key
CUBE_TEMPLATE_ID=your-template-id
CUBE_REMOTE_PROXY_VERIFY_SSL=false
```

Notes:

- OPENAI_API_KEY is required for embeddings, metadata extraction, and memory summarization
- TAVILY_API_KEY is required for latest-news ingestion
- REDIS_URL is required for Redis-backed research memory
- AWS_REGION is required for the Bedrock chat model path
- The sandbox feature can be enabled or switched between Cube and Modal depending on the deployment target

### Docker Compose

From the repo root:

```bash
docker-compose up --build
```

This starts:

- elasticsearch on 9200
- redis on 6379
- redis stack ui on 8001
- backend on 8000
- frontend on 5173

### Manual backend

```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Manual frontend

```bash
cd frontend
npm install
npm run dev
```

## Project structure

```text
backend/
  app/
    core/          configuration and path helpers
    db/            SQLite setup
    memory/        saved research history
    prompts/       metadata/domain prompts
    routers/       FastAPI routes
    services/      ingestion, retrieval, memory, sandbox, news, domains
    skills/        Deep Agent skill instructions
  storage/
    uploads/
    news_articles/
    outputs/
  main.py

frontend/
  src/
    components/
    pages/
    services/
```

## Practical summary

This project already uses the features you called out:

- Tavily for latest gold news search and extraction fallback
- Redis for persistent, searchable research memory
- Cube or Modal sandbox for isolated agent-driven document generation/editing
- OfficeCLI for office-document workflows inside the sandbox
- Elasticsearch for vector retrieval
- SQLite for metadata and semantic folder state
- APScheduler for daily automated news ingestion

In short, this is not just a chatbot README project. It is a document-and-news research workspace with semantic organization, scoped retrieval, agent analysis, memory, and optional sandboxed export tooling.