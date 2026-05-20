# 📄 AI-Powered Semantic Knowledge & RAG Platform

> Intelligent document management, adaptive semantic domains, automated news ingestion, and AI-powered multi-document reasoning.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?style=flat-square&logo=elasticsearch)](https://www.elastic.co)
[![LangChain](https://img.shields.io/badge/LangChain-Agent_Framework-blue?style=flat-square)](https://www.langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT_&_Embeddings-412991?style=flat-square&logo=openai)](https://openai.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)

---

# Overview

This project is an enterprise-style Retrieval-Augmented Generation (RAG) platform designed for intelligent document and knowledge management.

The system automatically:
- Ingests documents and online news
- Extracts structured metadata using LLMs
- Generates semantic embeddings
- Organizes documents into adaptive domains
- Performs semantic retrieval
- Enables grounded AI conversations across multiple sources

Unlike traditional RAG systems, this platform combines:
- Hybrid embeddings
- Adaptive domain centroids
- Metadata-aware semantic routing
- Multi-document reasoning
- Automated news ingestion pipelines

---

# Features

## 📤 Intelligent Document Ingestion
Supports:
- PDF
- DOCX
- TXT
- Markdown

Pipeline:
1. Text extraction
2. AI metadata extraction
3. Chunking
4. Embedding generation
5. Elasticsearch indexing
6. Automatic domain assignment

---

## 📰 Automated News Ingestion (Tavily Integration)

The platform integrates with Tavily to continuously ingest fresh online news.

### Workflow
1. Tavily searches the web
2. Retrieves the latest 10 relevant news articles
3. Downloads and extracts article content
4. Runs AI metadata extraction
5. Generates hybrid semantic embeddings
6. Compares semantic similarity against domain centroids
7. Automatically assigns the article into the most relevant domain

This allows the knowledge base to evolve dynamically with real-world information.

---

## 🤖 AI Metadata Extraction

The system automatically extracts:
- Title
- Focus/topic
- Keywords
- Entities
- Regions
- Economic indicators
- Publication date
- Context summaries

Metadata is used for:
- Retrieval
- Filtering
- Classification
- Semantic routing

---

# 🧠 Hybrid Embedding Architecture

One of the core innovations of the project.

Instead of relying only on document embeddings, the platform combines:

```python
hybrid_embedding =
(metadata_embedding * 0.7) +
(chunk_centroid_embedding * 0.3)
```

This improves:
- Semantic clustering
- Domain assignment
- Retrieval precision
- Search relevance

---

# 🧩 Adaptive Domain Centroid System

Domains are not static folders.

Each domain maintains a semantic centroid:

```python
domain_centroid =
average(all document embeddings inside the domain)
```

As more documents are added:
- Domains evolve automatically
- Semantic understanding improves
- Classification becomes more accurate

This creates a self-improving semantic organization system.

---

# 🔍 Semantic Search & Retrieval

Powered by:
- Elasticsearch vector search
- OpenAI embeddings
- Cosine similarity

Supports:
- Multi-document retrieval
- Domain-scoped search
- Global semantic querying
- Metadata-aware retrieval
- Chunk similarity matching

---

# 💬 Multi-Document RAG Agent

Built using LangChain.

The agent can:
- Retrieve relevant evidence
- Compare multiple sources
- Detect contradictions
- Summarize findings
- Generate grounded responses

Prompts are designed to:
- Reduce hallucinations
- Encourage analytical reasoning
- Force evidence grounding
- Support source attribution

---

# 🖥️ Frontend Features

Built with React + Vite.

Includes:
- AI chat interface
- Domain/folder navigation
- Upload modal
- Metadata editor
- Markdown AI rendering
- Multi-document querying
- Repository management UI

---

# 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                    React Frontend                         │
│  Chat UI · Uploads · Domains · Metadata · Repository      │
└───────────────────────┬────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                        │
│  Ingestion · Retrieval · RAG · Domains · Metadata         │
└───────────────────────┬────────────────────────────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   SQLite     │ │ Elasticsearch│ │ OpenAI APIs │
│ Metadata DB  │ │ Vector Store │ │ GPT + Embed │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

# 🛠️ Tech Stack

## Frontend
| Layer | Technology |
|------|-------------|
| Framework | React 19 |
| Build Tool | Vite |
| Styling | TailwindCSS |
| Rendering | Markdown Renderer |

---

## Backend
| Layer | Technology |
|------|-------------|
| Framework | FastAPI |
| Database | SQLite |
| Vector DB | Elasticsearch |
| AI Framework | LangChain |
| Embeddings | OpenAI |
| LLM | GPT Models |
| News Search | Tavily |
| Parsing | pypdf, python-docx |

---

# 📁 Project Structure

```bash
Internproject2/
├── backend/
│   ├── routers/
│   │   ├── ingest.py
│   │   ├── query.py
│   │   ├── news.py
│   │   └── documents.py
│   │
│   ├── services/
│   │   ├── document_ingestion_service.py
│   │   ├── retrieval_service.py
│   │   ├── rag_agent_service.py
│   │   ├── metadata_service.py
│   │   ├── hybrid_embedding_service.py
│   │   ├── domain_similarity_service.py
│   │   ├── domain_centroid_service.py
│   │   ├── news_ingestion_service.py
│   │   └── extraction_service.py
│   │
│   ├── prompts/
│   └── main.py
│
└── frontend/
    ├── components/
    │   ├── ChatWindow.jsx
    │   ├── SidebarFolders.jsx
    │   ├── UploadModal.jsx
    │   ├── MetadataModal.jsx
    │   └── DocumentRepository.jsx
    │
    └── Home.jsx
```

---

# 🔄 Full System Flow

```text
Upload File / Fetch News
            ↓
Text Extraction
            ↓
AI Metadata Extraction
            ↓
Chunking + Embeddings
            ↓
Hybrid Embedding Generation
            ↓
Elasticsearch Indexing
            ↓
Domain Similarity Matching
            ↓
Adaptive Centroid Assignment
            ↓
Semantic Retrieval
            ↓
RAG Agent Response Generation
```

---

# 📌 Core Technical Highlights

## ✅ Hybrid Semantic Routing
Combines:
- Metadata embeddings
- Document chunk centroid embeddings

for stronger semantic understanding.

---

## ✅ Adaptive Domain Intelligence
Domains continuously evolve as more documents are added.

---

## ✅ Multi-Document AI Reasoning
The RAG agent reasons across multiple sources instead of isolated QA.

---

## ✅ Automated News Knowledge Expansion
Fresh external news is automatically:
- collected
- processed
- embedded
- classified
- indexed

into the knowledge base.

---

# 🚀 Future Improvements

Potential upgrades:
- Streaming AI responses
- Redis caching
- Docker/Kubernetes deployment
- Fine-tuned local embeddings
- Knowledge graphs
- Real-time scheduled ingestion
- Multi-agent workflows
- User authentication

---

# 📄 Overall

This project goes beyond a basic chatbot or standard RAG demo.

It combines:
- Semantic search
- Hybrid embeddings
- Adaptive centroid intelligence
- AI metadata extraction
- Automated Tavily news ingestion
- Multi-document reasoning
- Enterprise-style retrieval architecture

to create an intelligent semantic knowledge management platform.
