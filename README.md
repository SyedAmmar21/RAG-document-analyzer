# 📄 AI-Powered RAG Document Assistant

> Intelligent document management with semantic search and AI-driven question answering.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?style=flat-square&logo=elasticsearch)](https://www.elastic.co)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5.4--nano-412991?style=flat-square&logo=openai)](https://openai.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-See%20LICENSE-blue?style=flat-square)](./LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Domain System](#domain-system)
- [Embedding Strategy](#embedding-strategy)
- [Testing](#testing)

---

## Overview

**AI-Powered RAG Document Assistant** is a full-stack web application for intelligent document management. Upload PDFs, TXT, or DOCX files, organize them into semantic knowledge domains, and query them using Retrieval-Augmented Generation (RAG).

The system combines **Elasticsearch** for vector-based semantic search with **OpenAI GPT** for metadata extraction, domain classification, and AI-powered question answering.

---

## Features

- 📤 **Document Upload** — Supports PDF, TXT, and DOCX with duplicate detection
- 🗂️ **Semantic Domains** — Auto-classify documents into knowledge clusters using LLM + cosine similarity
- 🤖 **RAG Question Answering** — Ask questions against specific documents or entire domains
- 🔍 **Field Search** — Extract specific metadata fields (entities, regions, indicators) on demand
- 🧾 **Metadata Extraction** — Automatic LLM-driven extraction of title, date, focus, and more
- 🗑️ **Document Management** — Full CRUD with metadata editing via UI modals

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        React Frontend                         │
│  (Vite + React 19 + TailwindCSS 4)                          │
│  - Document Repository   - Chat Window                       │
│  - Field Search          - Metadata Modal                    │
│  - Folder/Domain View    - File Upload                       │
└────────────────────────┬─────────────────────────────────────┘
                         │  HTTP / REST (fetch)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                          │
│  (Python 3.11+ · uv · pyproject.toml)                       │
│  /ingest · /query · /field-search · /documents · /domains   │
└────────────────────────┬─────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
   ┌─────────────┐ ┌───────────┐ ┌──────────────┐
   │   SQLite    │ │  Elastic- │ │  OpenAI API  │
   │  (metadata  │ │  search   │ │  GPT-5.4-    │
   │  documents  │ │ (vectors) │ │  nano +      │
   │  domains)   │ │           │ │  embeddings  │
   └─────────────┘ └───────────┘ └──────────────┘
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
| Package Manager | uv |
| Database | SQLite 3 |
| Vector DB | Elasticsearch (kNN) |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-5.4-nano` |
| Document Parsing | pypdf, python-docx |
| Agent Framework | LangChain 1.2+ |

---

## Project Structure

```
Internproject2/
├── backend/
│   ├── main.py                       # FastAPI app entry point
│   ├── pyproject.toml                # Python dependencies (uv)
│   ├── app/
│   │   ├── core/config.py            # Environment variable loading
│   │   ├── db/database.py            # SQLite init & schema
│   │   ├── prompts/
│   │   │   ├── domain_assignment_prompt.py
│   │   │   └── metadata_prompt.py
│   │   ├── routers/
│   │   │   ├── documents.py          # Document CRUD & metadata
│   │   │   ├── ingest.py             # File upload & deduplication
│   │   │   └── query.py              # RAG & field search
│   │   └── services/                 # 15 business logic services
│   ├── storage/
│   │   ├── uploads/                  # Uploaded document files
│   │   └── outputs/                  # Generated output files
│   └── tests/
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── pages/Home.jsx            # Main orchestrator page
        ├── components/
        │   ├── ChatWindow.jsx
        │   ├── DocumentRepository.jsx
        │   ├── FieldSearch.jsx
        │   ├── FileUpload.jsx
        │   ├── FoldersView.jsx
        │   ├── MarkdownMessage.jsx
        │   ├── MetadataModal.jsx
        │   ├── SidebarFolders.jsx
        │   └── UploadModal.jsx
        └── services/api.js           # Fetch-based API client
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Elasticsearch 8.x running on `localhost:9200`
- OpenAI API key

### Backend Setup

```bash
cd backend

# Install dependencies using uv
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your values (see Configuration section)

# Start the server
uvicorn main:app --reload
# → http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
# → http://localhost:5173
```

### Default Ports

| Service | Port |
|---------|------|
| Frontend (Vite) | 5173 |
| Backend (FastAPI) | 8000 |
| Elasticsearch | 9200 |

---

## Configuration

Create a `.env` file in the `backend/` directory:

```env
UPLOAD_DIR=/path/to/uploads
OUTPUT_DIR=/path/to/outputs
MAX_FILE_SIZE=5242880           # 5 MB in bytes
ELASTICSEARCH_HOST=http://localhost:9200
OPENAI_API_KEY=sk-...
```

| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_DIR` | Directory for uploaded files | — |
| `OUTPUT_DIR` | Directory for generated outputs | — |
| `MAX_FILE_SIZE` | Max upload size in bytes | `5242880` |
| `ELASTICSEARCH_HOST` | Elasticsearch URL | `http://localhost:9200` |
| `OPENAI_API_KEY` | OpenAI API key | — |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Upload and process a document |
| `POST` | `/query` | RAG-based AI question answering |
| `POST` | `/field-search` | Extract specific fields from a document |
| `GET` | `/documents` | List all documents |
| `DELETE` | `/documents/{id}` | Delete a document |
| `GET` | `/documents/{id}/metadata` | Get document metadata |
| `POST` | `/metadata` | Save or update document metadata |
| `GET` | `/domains` | List all semantic domains |
| `POST` | `/domains` | Create a new domain |
| `GET` | `/domains/{id}/documents` | Get documents in a domain |
| `GET` | `/unorganized` | Get unorganized documents |

### Example: Upload a Document

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@report.pdf"
```

```json
{
  "message": "Document uploaded successfully.",
  "document_id": "uuid",
  "file_name": "report.pdf",
  "duplicate": false,
  "metadata_suggestions": { "title": "...", "focus": "..." },
  "domain_suggestion": { "name": "Macroeconomics", "confidence": 0.85 }
}
```

### Example: RAG Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the impact of inflation on gold prices?", "document_id": "uuid"}'
```

```json
{
  "answer": "Based on the document, inflation..."
}
```

---

## Database Schema

The backend uses SQLite (`documents.db`) with four tables:

### `documents`
| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT (PK) | UUID |
| `created_date` | TEXT | ISO 8601 timestamp |
| `file_path` | TEXT | Absolute path to uploaded file |
| `meta_json` | TEXT | JSON: `{ file_size, file_type, ai_responses }` |

### `document_metadata`
| Column | Type | Description |
|--------|------|-------------|
| `document_id` | TEXT (FK) | References `documents.id` |
| `field` | TEXT | Field name (title, focus, entities, etc.) |
| `value` | TEXT | Field value (JSON array for list fields) |

### `domains`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-increment |
| `name` | TEXT | Domain name |
| `description` | TEXT | Domain description |
| `created_date` | TEXT | ISO 8601 timestamp |
| `embedding` | TEXT | JSON array (domain centroid vector) |

### `document_domains`
| Column | Type | Description |
|--------|------|-------------|
| `document_id` | TEXT | Document UUID |
| `domain_id` | INTEGER | Domain FK |
| `confidence` | REAL | Assignment confidence (0–1) |

---

## Domain System

Domains are **semantic knowledge clusters**, not physical folders. Documents are auto-assigned using a three-step process:

1. **Hybrid embedding** computed from document metadata + chunk vectors
2. **Cosine similarity** measured against existing domain centroids
3. **LLM-based classification** used as a secondary signal

Documents that don't meet the similarity threshold are placed in **Unorganized Files**.

### Default Domains

| Domain | Focus |
|--------|-------|
| Macroeconomics | Inflation, GDP, CPI, PPI, unemployment, economic growth |
| Central Banks | Federal Reserve, ECB, BOJ, PBOC, monetary policy |
| Geopolitics | Wars, sanctions, trade conflicts, political instability |

### Centroid Computation

```
Domain Centroid   = mean(document_centroid_1, document_centroid_2, ...)
Document Centroid = mean(chunk_embedding_1, chunk_embedding_2, ...)
```

---

## Embedding Strategy

Documents are indexed using a **hybrid embedding** that blends semantic metadata with content chunks:

```
Hybrid Vector = (metadata_embedding × 0.7) + (chunk_centroid × 0.3)
```

| Component | Weight | Source |
|-----------|--------|--------|
| Metadata embedding | 70% | title, focus, entities, indicators, regions |
| Chunk centroid | 30% | Mean of up to 5 chunk embeddings |

- **Model**: `text-embedding-3-small` (1536 dimensions)
- **Similarity**: Cosine
- **Storage**: Domain centroids → SQLite; chunk vectors → Elasticsearch

### Elasticsearch Index Mapping

```json
{
  "mappings": {
    "properties": {
      "document_id": { "type": "keyword" },
      "text":        { "type": "text" },
      "embedding": {
        "type":       "dense_vector",
        "dims":       1536,
        "index":      true,
        "similarity": "cosine"
      }
    }
  }
}
```

---

## Testing

Test files are in `backend/tests/`. Run individual test files using `uv`:

```bash
cd backend
uv run python tests/test_db.py
uv run python tests/test_index.py
uv run python tests/test_domain_similarity.py
```

| Test File | Purpose |
|-----------|---------|
| `test_api_endpoint.py` | API endpoint integration tests |
| `test_db.py` | Database operations |
| `test_document_centroid.py` | Document centroid computation |
| `test_domain_centroid.py` | Domain centroid computation |
| `test_domain_similarity.py` | Cosine similarity calculations |
| `test_index.py` | Elasticsearch index operations |
| `test_unorganized_endpoint.py` | Unorganized files endpoint |
| `check_unorganized.py` | Unorganized document count check |

---

## License

See [LICENSE](./LICENSE) for details.
