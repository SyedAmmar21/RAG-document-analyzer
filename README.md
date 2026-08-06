# Gold Analyst Helper: Adaptive Domain-Aware RAG platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF)](https://vite.dev/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8-005571)](https://www.elastic.co/elasticsearch/)
[![Redis](https://img.shields.io/badge/Redis%20Stack-red)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://www.docker.com/)

Gold Analyst Helper is a full-stack, domain-aware research workspace for gold-market documents and current news. It turns uploaded files and news articles into a searchable knowledge base, groups them into semantic folders, answers scoped research questions with a Deep Agent, retains high-value findings as research memory, and can generate or revise Office files in an isolated sandbox.

Although the product language and default domains are tailored to gold-market research, the document-ingestion, retrieval, and domain-organization architecture is reusable for other research collections.

## Contents

- [Capabilities](#capabilities)
- [How the workspace works](#how-the-workspace-works)
- [Active-document workflow](#active-document-workflow)
- [Architecture and tools](#architecture-and-tools)
- [Run locally](#run-locally)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Storage and project structure](#storage-and-project-structure)
- [Development and verification](#development-and-verification)

## Capabilities

### Research workspace

- Chat over all indexed research, selected semantic folders, or selected documents.
- Preserve a stable thread for the loaded workspace session, enabling agent state, sandbox reuse, and active-document continuity.
- Ask direct questions, summaries, comparisons, trend analyses, risk assessments, and executive-level research questions.
- Receive source-attributed, evidence-oriented answers that acknowledge uncertainty and evidence gaps.
- Upload PDF, DOCX, and TXT files up to the configured size limit (5 MB by default).
- Detect duplicate uploads by their original filename and reuse the existing repository record.

### Repository and metadata

- Browse the document repository with creation date, extracted publication date, assigned domains, and source URL where available.
- Open saved source documents inline, inspect metadata, use a document as a chat scope, or delete it.
- Review and save extracted metadata: title, publication date, focus, entities, economic indicators, and regions.
- Create, edit, and delete semantic folders (called **domains** in the backend). Deleting a folder leaves its documents available as **Unorganized Files**.

### Semantic organization and retrieval

- Chunk documents into overlapping 1,000-character passages and index passage vectors in Elasticsearch.
- Search by OpenAI `text-embedding-3-small` vector similarity, globally or within an explicit document list.
- Build hybrid document vectors from metadata (70%) and a centroid of the first five indexed chunks (30%).
- Assign new content to the closest semantic domain; if needed, fall back to metadata-driven domain selection.
- Recompute a domain centroid from its semantic description and assigned-document centroids after assignments or domain edits.
- Seed a new database with Macroeconomics, Central Banks, and Geopolitics domains.

### Current-news ingestion

- Find current gold-market news through Tavily using several targeted searches.
- Extract article text with Trafilatura, with Tavily Extract as a fallback.
- Deduplicate by canonical URL and normalized title, save each article as text, then run it through the same metadata, indexing, and domain-assignment pipeline as uploaded files.
- Trigger a manual ingestion from the chat workspace and see processed, skipped, and failed articles.
- Run scheduled ingestion daily at **10:00 AM Asia/Kuala_Lumpur** via APScheduler. The frontend polls for the one-time completion summary and refreshes the workspace.

### Agent, memory, and exports

- Use a Bedrock Claude Haiku Deep Agent with specialized retrieval, summarization, comparison, trend, risk, and synthesis tools.
- Save only worthwhile research results as compact long-term memory. Approved memories are appended to a Markdown research log and saved as independently searchable Redis records.
- Retrieve previous research when the question indicates memory or prior conclusions.
- Generate Word documents, spreadsheets, presentations, and PDFs through OfficeCLI in a provider-agnostic sandbox when sandbox support is configured.
- Keep generated files in an **Outputs** workspace, where users can open or delete them.

## How the workspace works

### 1. Upload and organize a document

1. In **Main**, choose the upload action and add a PDF, DOCX, or TXT file.
2. The API validates the extension and file size, checks for an existing filename, and stores a unique copy in `backend/storage/uploads`.
3. The backend extracts text with `pypdf`, `python-docx`, or UTF-8 text reading.
4. It creates a SQLite document record, extracts metadata with rules plus an LLM, and displays the suggestion in the metadata modal.
5. It chunks, embeds, and indexes the document in Elasticsearch.
6. It generates a hybrid document embedding, finds the closest domain, and saves the assignment. The document becomes the active retrieval scope in the UI.

If ingestion fails after the database record is created, the pipeline removes the record, metadata, assignment, and indexed chunks it created.

### 2. Scope and ask a research question

1. Select documents in **Repository** or documents/folders from the Main workspace sidebar.
2. The application uses document scope when any documents are selected, folder scope otherwise, and global scope when nothing is selected.
3. The query API turns selected folders into their current document IDs and gives the scoped IDs to the Deep Agent.
4. The agent chooses the appropriate tool(s): evidence retrieval, summary, document comparison, trend detection, risk analysis, or deep synthesis.
5. For questions about prior work, relevant Redis memories are inserted into the query context before the agent runs.
6. The final answer is returned to the chat and may be stored as long-term memory if the memory evaluator classifies it as strategically useful.

### 3. Ingest fresh gold news

1. Select **Download Latest Gold News** from Main, or let the scheduler run at its daily time.
2. Tavily returns candidate articles; duplicate URLs/titles are skipped.
3. Trafilatura extracts readable article text, falling back to Tavily extraction where necessary.
4. Every usable article is saved under `storage/news_articles` and processed through the normal document pipeline.
5. The UI reports processed, skipped, and failed articles and makes new articles available to select and query.

### 4. Create an Office output

1. Ask the agent to create a report, workbook, presentation, or PDF.
2. If sandbox support is enabled, the agent uses `sandbox_execute` and the OfficeCLI skill to work in `/workspace/output`.
3. Word reports use report-design guidance; Excel workbooks use workbook-design guidance. Presentation requests must first produce a validated slide plan, load the official recipe guidance, select a recipe for every slide, then pass structural validation and issue inspection.
4. The query post-processing copies generated files back to `backend/storage/outputs`, returns download links, and automatically makes editable Office outputs current for that thread.
5. Open, manage, or select the file in the **Outputs** tab.

## Active-document workflow

The active-document feature lets a chat continue editing one generated Office file rather than producing a new copy for every revision.

- Active files may be **DOCX, PPTX, or XLSX** only. PDFs can be opened or deleted but are not editable in this workflow.
- Active-document state is scoped to one chat thread. Each thread has at most one active file; different threads can keep independent active files.
- The agent automatically sets a newly generated editable output as active. Users can also choose **Set active** in the Outputs tab for an existing saved output.
- Selecting a saved output uploads it from persistent storage into that thread's sandbox at `/workspace/output/<filename>` before it is marked active. This ensures a newly created sandbox has the file to edit.
- On a follow-up edit request, the agent calls `get_current_document`, opens that sandbox copy, and modifies it with OfficeCLI. It is instructed to preserve existing content unless replacement is requested.
- After the agent run, changed sandbox outputs are copied back to `backend/storage/outputs`, where they appear in Outputs after refresh. Selecting **Active** again deselects the file. Deleting a file clears any stale active reference to it.

This feature depends on a configured sandbox provider. See [Configuration](#configuration) and the detailed [active-output design note](docs/active-output-documents.md).

## Architecture and tools

| Layer | Tools and responsibilities |
| --- | --- |
| Frontend | React 19, Vite 8, plain CSS, and the browser Fetch API. Provides Main, Repository, Folders, and Outputs views. |
| API | FastAPI with CORS enabled for the local Vite server; Uvicorn serves the application. |
| Primary database | SQLite stores documents, extracted metadata, domains, and document-domain assignments. |
| Vector search | Elasticsearch 8 stores chunk text and 1,536-dimension `text-embedding-3-small` vectors for kNN cosine search. |
| Embeddings and metadata | OpenAI embeddings power retrieval and semantic grouping. `gpt-5.4-nano` augments rule-based metadata extraction and decides/summarizes durable memories. |
| Agent orchestration | DeepAgents, LangChain, and LangGraph. The primary response model is Bedrock `global.anthropic.claude-haiku-4-5-20251001-v1:0`; prompt caching middleware is enabled. |
| Research memory | Redis Stack with LangGraph `RedisStore` keeps searchable memory records; an append-only Markdown history is retained locally. |
| News | Tavily provides discovery/extraction fallback; Trafilatura extracts article content. APScheduler runs daily ingestion. |
| Document sandbox | Cube/E2B or Modal provides isolated, thread-reused execution. OfficeCLI handles Office files; provider-specific backends share one interface. |
| Document libraries | `pypdf`, `python-docx`, `openpyxl`, `python-pptx`, and `reportlab` support document handling and legacy/export paths. |
| Containers | Docker Compose starts Elasticsearch, Redis Stack, FastAPI, and the Vite frontend. |

### Agent tools

The Deep Agent can select the following backend tools:

- `search_documents_tool` — retrieve the most relevant chunks as evidence.
- `summarize_document_tool` — produce a focused document overview.
- `compare_documents_tool` — identify agreement, disagreement, and complementary perspectives.
- `identify_trends_tool` — find recurring themes, patterns, and cause/effect signals.
- `risk_analysis_tool` — surface uncertainty, conflicts, weaknesses, and risks.
- `deep_research_tool` — synthesize multi-step research into executive findings.
- `research_memory_tool` — search saved research memories.
- `sandbox_execute` — run approved shell/OfficeCLI work in the configured sandbox.
- `create_presentation_plan`, `load_presentation_recipe_guidance`, `select_presentation_recipes`, and `qa_presentation` — the mandatory PowerPoint control plane.
- `get_current_document` — find the thread's active Office document before an edit.

The agent's built-in skills cover retrieval strategy, comparative and analytical review, memory-aware analysis, report and workbook design, presentation planning/design/recipe selection, and OfficeCLI. These instructions guide tool choice and output quality; OfficeCLI remains the authority for OfficeCLI command syntax.

## Run locally

### Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for the backend workflow
- Node.js 18 or newer (the frontend Docker image uses Node 24)
- Docker Desktop for the Compose workflow
- Credentials for the external services you intend to enable

### 1. Configure the backend

Create `backend/.env`:

```env
# Required for embeddings, metadata extraction, and memory evaluation
OPENAI_API_KEY=your-openai-key

# Use this local value when running the API outside Docker.
ELASTICSEARCH_HOST=http://localhost:9200
TAVILY_API_KEY=your-tavily-key
REDIS_URL=redis://localhost:6379
AWS_REGION=your-aws-region
MAX_FILE_SIZE=5242880

# Choose one optional document sandbox provider.
# Cube is enabled when both settings are present.
SANDBOX_PROVIDER=cube
CUBE_TEMPLATE_ID=your-template-id
E2B_API_URL=https://your-cube-endpoint
E2B_API_KEY=your-cube-api-key

# Or use Modal instead.
# SANDBOX_PROVIDER=modal
# USE_MODAL_SANDBOX=true
# MODAL_APP_NAME=your-modal-app

# Optional: pin an OfficeCLI installer version.
# OFFICECLI_VERSION=...
```

For Docker Compose, use service names instead:

```env
ELASTICSEARCH_HOST=http://elasticsearch:9200
REDIS_URL=redis://rag-redis:6379
```

`OPENAI_API_KEY` is needed by the core ingestion and retrieval flow. `TAVILY_API_KEY` is needed only for latest-news ingestion; `AWS_REGION` is needed for the Bedrock agent path. Sandbox-backed generation and active-document editing are optional: Cube requires `SANDBOX_PROVIDER=cube` and `CUBE_TEMPLATE_ID`; Modal requires `SANDBOX_PROVIDER=modal` and `USE_MODAL_SANDBOX=true` plus usable Modal credentials.

Optionally create `frontend/.env.local` when the API is not at its default address:

```env
VITE_API_URL=http://127.0.0.1:8000
```

### 2. Start with Docker Compose

From the repository root:

```bash
docker-compose up --build
```

Services are exposed at:

| Service | Address |
| --- | --- |
| Frontend | http://localhost:5173 |
| FastAPI | http://localhost:8000 |
| Elasticsearch | http://localhost:9200 |
| Redis | `redis://localhost:6379` |
| Redis Stack UI | http://localhost:8001 |

The Compose file persists Elasticsearch and Redis data in named volumes. It also mounts backend storage, SQLite data, and the Markdown memory log so those project data survive container replacement. Its Modal credential mount is a Windows-specific path; adjust or remove it for another host or when Modal is not used.

### 3. Or start the services manually

Start Elasticsearch and Redis Stack first, then run the API:

```bash
cd backend
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Configuration

| Variable | Purpose | Default / requirement |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI embeddings, metadata enrichment, memory evaluation/summarization | Required for core RAG operation |
| `ELASTICSEARCH_HOST` | Elasticsearch endpoint | Required by retrieval; vector service defaults to `http://elasticsearch:9200` |
| `TAVILY_API_KEY` | Gold-news discovery and extraction fallback | Required for news ingestion |
| `REDIS_URL` | LangGraph Redis store endpoint | Defaults to `redis://rag-redis:6379` |
| `AWS_REGION` | Region used by Bedrock Claude | Needed for agent requests |
| `MAX_FILE_SIZE` | Maximum upload size in bytes | `5242880` (5 MB) |
| `SANDBOX_PROVIDER` | `cube` or `modal` | `modal` |
| `CUBE_TEMPLATE_ID` | Enables Cube sandbox path | Required for Cube |
| `E2B_API_URL`, `E2B_API_KEY` | Cube/E2B connection details | Required by the Cube service |
| `USE_MODAL_SANDBOX` | Enables Modal sandbox path | `false` |
| `MODAL_APP_NAME` | Modal application name | `sandbox-learning` |
| `OFFICECLI_VERSION` | Optional OfficeCLI installer pin | Latest installer script when omitted |
| `VITE_API_URL` | Frontend API base URL | `http://127.0.0.1:8000` |

## API reference

The API currently has no authentication layer and is configured for local development origins (`localhost:5173` and `127.0.0.1:5173`). Do not expose it publicly without adding authentication, authorization, restrictive CORS, secret management, and production operational controls.

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/ingest` | Validate, store, extract, index, and semantically assign one uploaded file. |
| `POST` | `/reindex` | Re-run the ingestion pipeline across saved documents. |
| `POST` | `/query` | Run the Deep Agent with global, folder, document, or legacy single-document scope. |
| `POST` | `/news/ingest-latest` | Find and ingest the latest gold news. |
| `GET` | `/news/scheduled-summary` | Consume the most recent scheduled-ingestion summary. |
| `GET` | `/documents` | List repository documents. |
| `DELETE` | `/documents/{document_id}` | Remove a document, source file, metadata, domain assignment, and indexed chunks. |
| `GET` | `/documents/{document_id}/view` | Open a stored source document inline. |
| `GET` | `/documents/{document_id}/metadata` | Get saved metadata and its domain assignment. |
| `POST` | `/documents/{document_id}/metadata` | Save metadata and optionally assign a domain. |
| `POST` | `/metadata/save` | Save metadata through the modal workflow. |
| `GET` | `/domains` | List semantic domains and synthetic Unorganized Files when relevant. |
| `GET` | `/domains/{domain_id}/documents` | List documents in one domain, including `unorganized`. |
| `POST` | `/domains` | Create a semantic domain. |
| `PUT` | `/domains/{domain_id}` | Update a domain and recompute its centroid. |
| `DELETE` | `/domains/{domain_id}` | Delete a domain and move its documents to Unorganized Files. |
| `GET` | `/outputs` | List generated output files and whether each is editable. |
| `GET` | `/outputs/active?thread_id=...` | Get the thread's active Office document. |
| `PUT` | `/outputs/active` | Upload a saved Office output to the thread sandbox and set it active. |
| `DELETE` | `/outputs/active?thread_id=...` | Clear the thread's active document. |
| `GET` | `/outputs/{filename}/view` | Open an output inline. |
| `DELETE` | `/outputs/{filename}` | Delete an output and clear active references. |
| `GET` | `/download/{filename}` | Download a generated output as an attachment. |
| `POST` | `/generate-presentation` | Deprecated legacy route; deliberately returns a conflict response. |

Example active-document request:

```json
PUT /outputs/active
{
  "thread_id": "chat-thread-id",
  "file_name": "gold-market-report.docx"
}
```

## Storage and project structure

```text
backend/
  app/
    core/                   configuration and safe storage-path helpers
    db/                     SQLite schema and setup
    memory/                 append-only saved research history
    prompts/                metadata and domain-assignment prompts
    routers/                query, ingestion, news, documents, outputs, domains
    services/               RAG, metadata, memory, retrieval, news, sandbox, domains
    skills/                 agent guidance for research and Office workflows
  storage/
    uploads/                source files uploaded by users
    news_articles/          saved current-news text files
    outputs/                persistent agent-generated artifacts
  main.py                   FastAPI application and scheduler lifecycle

frontend/
  src/
    components/             chat, repository, folders, outputs, modals
    pages/Home.jsx          workspace state, thread ID, scopes, and tabs
    services/api.js         backend client

docs/
  active-output-documents.md  active-document design and manual test checklist
  ...                         sandbox and architecture notes

docker-compose.yml          local multi-service environment
```

Persistent application data lives at:

- `backend/app/db/documents.db` — SQLite document, metadata, and domain state.
- `backend/storage/uploads` — user-uploaded source files.
- `backend/storage/news_articles` — ingested news article text files.
- `backend/storage/outputs` — generated or revised agent artifacts.
- `backend/app/memory/research_history.md` — local long-term research history.

## Development and verification

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

Backend test utilities live in `backend/` and include database, vector-index, API, domain-centroid/similarity, agent, and unorganized-folder checks. Run the relevant script with the backend environment and dependencies available, for example:

```bash
cd backend
uv run python test_db.py
uv run python test_index.py
```

For active-document changes, follow the manual verification checklist in [docs/active-output-documents.md](docs/active-output-documents.md): generate an editable file, activate it, revise it through the chat, confirm it refreshes in Outputs, then confirm deselection/deletion removes its active state.

## Notes and limitations

- Text extraction supports PDF, DOCX, and TXT uploads; scanned PDFs without an extractable text layer will fail ingestion.
- Duplicate detection is filename-based, not file-content-based.
- Active-document edits require a working Cube or Modal sandbox plus OfficeCLI; no active PDF editing path is implemented.
- Scheduled-ingestion results are held in process memory and are intentionally consumed after the frontend retrieves them once.
- The project is currently a local-development workspace, not a hardened multi-user deployment.

## License

This project is distributed under the [MIT License](LICENSE).
