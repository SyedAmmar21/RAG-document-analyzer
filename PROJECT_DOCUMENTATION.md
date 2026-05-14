# AI-Powered RAG Document Assistant — Project Documentation

> **Version:** 0.1.0
> **Last Updated:** May 14, 2026

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Backend Documentation](#backend-documentation)
6. [Frontend Documentation](#frontend-documentation)
7. [Data Flow](#data-flow)
8. [API Reference](#api-reference)
9. [Database Schema](#database-schema)
10. [Services Layer](#services-layer)
11. [Configuration](#configuration)
12. [Running the Project](#running-the-project)
13. [Domain System](#domain-system)
14. [Embedding Strategy](#embedding-strategy)

---

## Project Overview

**AI-Powered RAG Document Assistant** is a full-stack web application that enables users to:

- Upload documents (PDF, TXT, DOCX)
- Organize them into semantic knowledge domains (folders)
- Query documents using AI-powered Retrieval-Augmented Generation (RAG)
- Extract and manage document metadata
- Search across specific fields within documents

The system uses **Elasticsearch** for vector-based semantic search and **OpenAI GPT** for metadata extraction, domain classification, and RAG-based question answering.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        React Frontend                         │
│  (Vite + React 19 + TailwindCSS 4)                          │
│  - Document Repository   - Chat Window                      │
│  - Field Search          - Metadata Modal                   │
│  - Folder/Domain View    - File Upload                      │
└────────────────────────┬─────────────────────────────────────┘
                         │  HTTP / REST (fetch)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                          │
│  (Python 3.11+ · uv · pyproject.toml)                       │
│  - /ingest      - Document ingestion & duplicate detection   │
│  - /query       - RAG-based AI question answering           │
│  - /field-search - Field-specific information extraction    │
│  - /documents   - CRUD for documents & metadata             │
│  - /domains     - Domain (folder) management                │
└────────────────────────┬─────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
   ┌─────────────┐ ┌──────────┐ ┌──────────────┐
   │  SQLite     │ │Elastic-  │ │  OpenAI API  │
   │  (metadata) │ │  search  │ │ (GPT-5.4-    │
   │  (documents│ │  (vectors)│ │  nano, text-  │
   │   , domains│ │           │ │  embedding-3) │
   │   , meta)  │ │           │ │              │
   └─────────────┘ └──────────┘ └──────────────┘
```

---

## Tech Stack

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React 19 |
| Build Tool | Vite 8 |
| Styling | TailwindCSS 4 + PostCSS + Autoprefixer |
| Linting | ESLint 10 + eslint-plugin-react-hooks |
| Markdown | Custom Markdown renderer |

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.136+ |
| Server | Uvicorn 0.46+ |
| Package Manager | uv (Python) |
| Database | SQLite 3 (metadata) |
| Vector DB | Elasticsearch (kNN vector search) |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | OpenAI GPT-5.4-nano |
| Document Parsing | pypdf, python-docx |
| Agent Framework | LangChain 1.2+ |

---

## Project Structure

```
Internproject2/
├── LICENSE
├── README.md
│
├── backend/                          # FastAPI Backend
│   ├── pyproject.toml                # Python dependencies (uv)
│   ├── main.py                       # FastAPI app entry point
│   ├── README.md                     # (empty)
│   │
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py             # Environment variable loading
│   │   │
│   │   ├── db/
│   │   │   └── database.py           # SQLite init, schema, connections
│   │   │
│   │   ├── models/                   # (empty — Pydantic models inline)
│   │   │
│   │   ├── prompts/
│   │   │   ├── domain_assignment_prompt.py   # LLM prompt for domain classification
│   │   │   └── metadata_prompt.py            # LLM prompt for metadata extraction
│   │   │
│   │   ├── routers/
│   │   │   ├── documents.py          # Document CRUD, metadata save, domain management
│   │   │   ├── ingest.py             # File upload, validation, deduplication
│   │   │   └── query.py              # RAG query & field search endpoints
│   │   │
│   │   └── services/                 # Business logic layer (15 services)
│   │       ├── document_centroid_service.py    # Document-level vector centroid
│   │       ├── document_service.py             # Document CRUD operations
│   │       ├── domain_assignment_service.py    # LLM-based domain assignment
│   │       ├── domain_centroid_service.py      # Domain-level vector centroid
│   │       ├── domain_service.py               # Domain CRUD & management
│   │       ├── domain_similarity_service.py    # Cosine similarity for domain matching
│   │       ├── extraction_service.py           # LLM-based field extraction
│   │       ├── file_service.py                 # File validation & saving
│   │       ├── hybrid_embedding_service.py     # Metadata + chunk hybrid embeddings
│   │       ├── metadata_extraction_service.py  # LLM + heuristic metadata extraction
│   │       ├── metadata_service.py             # Metadata CRUD & validation
│   │       ├── rag_agent_service.py            # LangChain RAG agent
│   │       ├── retrieval_service.py            # Elasticsearch kNN search
│   │       ├── text_extraction_service.py      # PDF/TXT/DOCX text extraction
│   │       └── vector_service.py               # Elasticsearch index & embeddings
│   │
│   ├── storage/
│   │   ├── outputs/                    # Generated output files
│   │   └── uploads/                    # Uploaded document files
│   │
│   └── tests/                          # Test files
│       ├── check_unorganized.py
│       ├── test_api_endpoint.py
│       ├── test_db.py
│       ├── test_document_centroid.py
│       ├── test_domain_centroid.py
│       ├── test_domain_similarity.py
│       ├── test_index.py
│       ├── test_unorganized_endpoint.py
│       └── tests.py
│
└── frontend/                           # React Frontend
    ├── package.json                    # Node dependencies
    ├── vite.config.js                  # Vite configuration
    ├── eslint.config.js                # ESLint configuration
    ├── index.html                      # Entry HTML
    │
    ├── public/                         # Static assets
    │
    └── src/
        ├── main.jsx                    # React entry point
        ├── App.jsx                     # Root component (Home)
        ├── App.css                     # Global styles
        ├── index.css                   # Tailwind imports
        │
        ├── pages/
        │   └── Home.jsx                # Main page — orchestrates all components
        │
        ├── components/
        │   ├── ChatWindow.jsx           # AI chat interface
        │   ├── DocumentRepository.jsx   # Document list/table
        │   ├── FieldSearch.jsx          # Field-specific metadata extraction
        │   ├── FileUpload.jsx           # Inline file upload panel
        │   ├── FoldersView.jsx          # Domain/folder browser
        │   ├── MarkdownMessage.jsx      # Custom Markdown renderer
        │   ├── MetadataModal.jsx        # Metadata editing modal
        │   ├── SidebarFolders.jsx       # Left sidebar domain navigation
        │   └── UploadModal.jsx          # Modal file upload
        │
        └── services/
            └── api.js                   # API client (fetch wrappers)
```

---

## Backend Documentation

### Entry Point — `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db

app = FastAPI()
init_db()  # Creates SQLite DB + tables if not exists

# Routers
app.include_router(ingest_router)    # /ingest
app.include_router(query_router)     # /query, /field-search
app.include_router(documents_router) # /documents, /domains, /metadata

# CORS
app.add_middleware(CORSMiddleware, ...)  # Allows localhost:5173
```

### Configuration — `app/core/config.py`

All configuration is loaded from environment variables via `python-dotenv`:

| Variable | Purpose |
|----------|---------|
| `UPLOAD_DIR` | Directory for uploaded files |
| `OUTPUT_DIR` | Directory for generated outputs |
| `MAX_FILE_SIZE` | Max upload size in bytes (default 5MB) |
| `ELASTICSEARCH_HOST` | Elasticsearch URL (e.g., `http://localhost:9200`) |
| `OPENAI_API_KEY` | OpenAI API key for embeddings & LLM |

### Routers

#### 1. `ingest_router` — `/ingest` (POST)

Handles document ingestion with deduplication.

**Flow:**
1. Validate file type (`.pdf`, `.txt`, `.docx`)
2. Validate file size (≤ MAX_FILE_SIZE)
3. Check for duplicate uploads
4. If duplicate → return existing document info
5. If new → save file, extract text, generate embeddings, extract metadata, assign domain, index in Elasticsearch

**Response (new file):**
```json
{
  "message": "Document uploaded successfully.",
  "document_id": "uuid",
  "file_name": "example.pdf",
  "file_path": "/path/to/uploads/example_edited.pdf",
  "document_number": 1,
  "duplicate": false,
  "metadata_suggestions": { ... },
  "domain_suggestion": { "name": "...", "confidence": 0.85 }
}
```

**Response (duplicate):**
```json
{
  "message": "This file is already in the repository...",
  "document_id": "existing-uuid",
  "duplicate": true,
  "metadata_suggestions": { ... },
  "domain_suggestion": { "name": "...", "confidence": 0.85 }
}
```

#### 2. `query_router` — `/query` (POST) & `/field-search` (POST)

**`/query` — RAG-based Question Answering:**
```json
// Request
{ "query": "What is the impact of inflation on gold prices?", "document_id": "uuid" }

// Response
{ "answer": "Based on the document..." }
```

**`/field-search` — Field-specific Extraction:**
```json
// Request
{ "fields": ["entities", "regions"], "document_id": "uuid" }

// Response
{ "entities": ["Federal Reserve", "ECB"], "regions": ["United States", "Europe"] }
```

#### 3. `documents_router` — `/documents` (GET), `/domains` (GET/POST), `/metadata` (POST)

**`GET /documents`** — List all documents
**`GET /domains`** — List all semantic domains (folders)
**`POST /domains`** — Create a new domain
**`POST /metadata`** — Save/update document metadata
**`DELETE /documents/{id}`** — Delete a document

---

## Frontend Documentation

### Entry Point — `main.jsx`

```jsx
import { createRoot } from "react-dom/client";
import App from "./App";
createRoot(document.getElementById("root")).render(<App />);
```

### Root Component — `App.jsx`

```jsx
import Home from "./pages/Home";
function App() { return <Home />; }
```

### Main Page — `Home.jsx`

The central orchestrator component that manages:
- Active document state
- Metadata suggestions
- Domain suggestions
- Tab navigation (main / repository / folders)
- Upload modal state
- Metadata modal state
- Retrieval scope (global vs. folder/document-scoped)

### Components

| Component | Purpose |
|-----------|---------|
| `ChatWindow` | AI chat interface with message history, scope badge, retrieval scope selector |
| `DocumentRepository` | Table view of all documents with search, delete, and select actions |
| `FieldSearch` | Metadata editing form with domain assignment and domain creation |
| `FileUpload` | Inline file upload panel (drag & drop / file picker) |
| `FoldersView` | Domain/folder browser with document listing per folder |
| `MarkdownMessage` | Custom Markdown renderer (bold, italic, code, lists, tables, code blocks) |
| `MetadataModal` | Modal dialog for editing document metadata and domain assignment |
| `SidebarFolders` | Left sidebar with expandable domain tree |
| `UploadModal` | Modal dialog for file upload |

### API Client — `services/api.js`

Wraps all backend API calls using native `fetch`:

| Function | Endpoint | Method |
|----------|----------|--------|
| `uploadFile(file)` | `/ingest` | POST |
| `queryAgent(query, document_id)` | `/query` | POST |
| `searchFields(fields, document_id)` | `/field-search` | POST |
| `getDocuments()` | `/documents` | GET |
| `deleteDocument(id)` | `/documents/{id}` | DELETE |
| `getDomains()` | `/domains` | GET |
| `createDomain(data)` | `/domains` | POST |
| `saveDocumentMetadata(data)` | `/metadata` | POST |
| `getFolderDocuments(folder_id)` | `/domains/{id}/documents` | GET |
| `getDocumentMetadata(doc_id)` | `/documents/{id}/metadata` | GET |

---

## Data Flow

### Document Ingestion Pipeline

```
User uploads file
       │
       ▼
File Validation (type, size)
       │
       ▼
Duplicate Check (by filename pattern)
       │
       ▼
  [If duplicate] → Return existing doc info
       │
  [If new]
       │
       ▼
Save File → uploads/
       │
       ▼
Extract Text (PDF/TXT/DOCX)
       │
       ▼
Chunk Text (1000 chars, 200 overlap)
       │
       ▼
Generate Hybrid Embedding
  ├─ Metadata embedding (weight: 0.7)
  └─ Chunk centroid embedding (weight: 0.3)
       │
       ▼
Extract Metadata (LLM)
  ├─ title
  ├─ published_date
  ├─ focus
  ├─ entities
  ├─ economic_indicators
  └─ regions
       │
       ▼
Assign Domain (LLM cosine similarity)
       │
       ▼
Index in Elasticsearch (kNN vector index)
       │
       ▼
Create SQLite record (documents table)
       │
       ▼
Return response to frontend
```

### RAG Query Pipeline

```
User sends query
       │
       ▼
LangChain Agent created (per document)
       │
       ▼
Agent has 2 tools:
  1. search_documents_tool → Elasticsearch kNN (top_k=4)
  2. summarize_document_tool → Elasticsearch kNN (top_k=8) + LLM summary
       │
       ▼
LLM (GPT-5.4-nano) generates answer
       │
       ▼
Save AI response to SQLite (ai_responses)
       │
       ▼
Return answer to frontend
```

---

## API Reference

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest` | Upload and process a document |
| POST | `/query` | RAG-based AI question answering |
| POST | `/field-search` | Extract specific fields from document |
| GET | `/documents` | List all documents |
| DELETE | `/documents/{id}` | Delete a document |
| GET | `/domains` | List all domains (folders) |
| POST | `/domains` | Create a new domain |
| GET | `/domains/{id}/documents` | Get documents in a domain |
| POST | `/metadata` | Save document metadata |
| GET | `/documents/{id}/metadata` | Get document metadata |
| GET | `/unorganized` | Get unorganized documents |

---

## Database Schema

### SQLite — `documents.db`

#### `documents` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | UUID |
| `created_date` | TEXT | ISO 8601 (Malaysia timezone) |
| `file_path` | TEXT | Absolute path to uploaded file |
| `meta_json` | TEXT | JSON: `{ file_size, file_type, ai_responses }` |

#### `document_metadata` table
| Column | Type | Description |
|--------|------|-------------|
| `document_id` | TEXT (FK) | References documents.id |
| `field` | TEXT | Field name (title, focus, entities, etc.) |
| `value` | TEXT | Field value (JSON array for list fields) |

#### `domains` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-increment |
| `name` | TEXT | Domain name |
| `description` | TEXT | Domain description |
| `created_date` | TEXT | ISO 8601 |
| `embedding` | TEXT | JSON array (domain centroid vector) |

#### `document_domains` table
| Column | Type | Description |
|--------|------|-------------|
| `document_id` | TEXT | Document UUID |
| `domain_id` | INTEGER | Domain FK |
| `confidence` | REAL | Assignment confidence (0-1) |

---

## Services Layer

### 15 Backend Services

| Service | Responsibility |
|---------|---------------|
| `document_service.py` | Document CRUD, UUID generation, duplicate detection |
| `file_service.py` | File validation (type/size), save to uploads/ |
| `text_extraction_service.py` | Extract text from PDF, TXT, DOCX |
| `hybrid_embedding_service.py` | Generate hybrid embeddings (metadata 70% + chunks 30%) |
| `vector_service.py` | Elasticsearch index management, chunking, kNN search |
| `retrieval_service.py` | Elasticsearch kNN document chunk retrieval |
| `metadata_extraction_service.py` | LLM + heuristic metadata extraction (title, date, entities, etc.) |
| `metadata_service.py` | Metadata CRUD, validation, normalization |
| `domain_service.py` | Domain CRUD, document-domain mapping, unorganized count |
| `domain_assignment_service.py` | LLM-based domain classification |
| `domain_similarity_service.py` | Cosine similarity for domain matching |
| `domain_centroid_service.py` | Recompute domain centroid from document vectors |
| `document_centroid_service.py` | Compute document centroid from chunk vectors |
| `extraction_service.py` | LLM-based field extraction from document chunks |
| `rag_agent_service.py` | LangChain agent with search + summarize tools |

### Prompt Engineering

Two LLM prompts drive the AI features:

1. **`metadata_prompt.py`** — Extracts structured metadata (title, focus, entities, economic_indicators, regions) from document text
2. **`domain_assignment_prompt.py`** — Assigns documents to semantic domains based on metadata

Both use `ChatOpenAI(model="gpt-5.4-nano")`.

---

## Configuration

### Environment Variables (`.env`)

```env
UPLOAD_DIR=/path/to/uploads
OUTPUT_DIR=/path/to/outputs
MAX_FILE_SIZE=5242880
ELASTICSEARCH_HOST=http://localhost:9200
OPENAI_API_KEY=sk-...
```

### Elasticsearch Index Mapping

```json
{
  "mappings": {
    "properties": {
      "document_id": { "type": "keyword" },
      "text": { "type": "text" },
      "embedding": {
        "type": "dense_vector",
        "dims": 1536,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
```

---

## Running the Project

### Prerequisites

- Python 3.11+
- Node.js 18+
- Elasticsearch 8.x (running on localhost:9200)
- OpenAI API key

### Backend Setup

```bash
cd backend
uv sync
# Copy .env.example to .env and configure
uvicorn main:app --reload    # Starts on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev                  # Starts on http://localhost:5173
```

### Default Ports

| Service | Port |
|---------|------|
| Frontend (Vite) | 5173 |
| Backend (FastAPI/Uvicorn) | 8000 |
| Elasticsearch | 9200 |

---

## Domain System

Domains are **semantic knowledge clusters** (not physical folders). Documents are assigned to domains using:

1. **Hybrid embedding** of document metadata + chunk vectors
2. **Cosine similarity** against domain centroids
3. **LLM-based classification** as a secondary signal

### Default Domains

| Domain | Description |
|--------|-------------|
| Macroeconomics | Inflation, GDP, CPI, PPI, unemployment, economic growth |
| Central Banks | Federal Reserve, ECB, BOJ, PBOC, monetary policy |
| Geopolitics | Wars, sanctions, trade conflicts, political instability |

### Domain Centroid Computation

```
Domain Centroid = mean(document_centroid_1, document_centroid_2, ...)
Document Centroid = mean(chunk_embedding_1, chunk_embedding_2, ...)
```

### Unorganized Files

Documents that don't meet a similarity threshold are placed in a synthetic "Unorganized Files" folder.

---

## Embedding Strategy

### Hybrid Embedding Formula

```
Hybrid Vector = (metadata_embedding × 0.7) + (chunk_centroid × 0.3)
```

- **Metadata embedding**: Built from title, focus, entities, economic_indicators, regions
- **Chunk centroid**: Mean of up to 5 document chunk embeddings
- **Model**: `text-embedding-3-small` (1536 dimensions)
- **Similarity**: Cosine similarity

### Vector Storage

- **SQLite**: Domain centroids (JSON arrays)
- **Elasticsearch**: Document chunk vectors (dense_vector field)

---

## Testing

Test files are located in `backend/tests/`:

| Test File | Purpose |
|-----------|---------|
| `test_api_endpoint.py` | API endpoint testing |
| `test_db.py` | Database operations |
| `test_document_centroid.py` | Document centroid computation |
| `test_domain_centroid.py` | Domain centroid computation |
| `test_domain_similarity.py` | Cosine similarity calculations |
| `test_index.py` | Elasticsearch index operations |
| `test_unorganized_endpoint.py` | Unorganized files endpoint |
| `check_unorganized.py` | Check unorganized document count |

Run tests with:
```bash
cd backend
uv run python tests/test_db.py
uv run python tests/test_index.py
# etc.
```
