# 📄 Adaptive Domain-Aware RAG Platform

> An enterprise-grade intelligent document management system combining adaptive semantic domains, hybrid embeddings, automated news ingestion, and AI-powered knowledge reasoning.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?style=flat-square&logo=elasticsearch)](https://www.elastic.co)
[![LangChain](https://img.shields.io/badge/LangChain-Agent_Framework-blue?style=flat-square)](https://www.langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT_&_Embeddings-412991?style=flat-square&logo=openai)](https://openai.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)

---

# Overview

This is an enterprise-level Retrieval-Augmented Generation (RAG) platform that reimagines semantic knowledge management through adaptive domain learning. Rather than static document organization, the system continuously learns and refines semantic domain understanding as documents are ingested and processed.

The platform automatically:
- Ingests and processes documents and online news
- Extracts rich structured metadata using LLMs
- Generates hybrid semantic embeddings
- Organizes documents into adaptive, evolving domains
- Performs intelligent multi-document retrieval
- Enables grounded, evidence-based AI conversations

**Core Differentiators:**
- Adaptive domain centroids that evolve with document ingestion
- Hybrid embedding architecture combining metadata and content signals
- Domain-aware retrieval using cosine similarity matching
- Automated news pipeline with Tavily integration
- Multi-document reasoning with source attribution

---

# Key Features

## 🚀 Intelligent Document Ingestion

Comprehensive support for multiple document formats:
- **Formats:** PDF, DOCX, TXT, Markdown
- **Pipeline:** Text extraction → Metadata extraction → Semantic embedding → Hybrid encoding → Elasticsearch indexing → Adaptive domain assignment
- **Metadata Enrichment:** Automatic extraction of titles, keywords, entities, publication dates, and semantic context

## 📡 Automated News Ingestion Pipeline

Integrates Tavily for real-time knowledge base expansion:
1. **News Retrieval:** Tavily searches and retrieves latest relevant articles
2. **Content Processing:** Article text and metadata extraction
3. **Semantic Enhancement:** Hybrid embedding generation
4. **Domain Classification:** Intelligent matching against adaptive domain centroids
5. **Automatic Indexing:** Articles are indexed and assigned to appropriate domains

This enables the knowledge base to evolve dynamically with external information sources.

## 🧠 AI-Powered Metadata Extraction

Intelligent extraction of structured information:
- Titles and focus areas
- Keywords and topics
- Named entities and regions
- Economic indicators and metrics
- Publication metadata
- Contextual summaries

Metadata drives downstream:
- Semantic routing decisions
- Retrieval precision
- Domain classification accuracy
- Evidence grounding

## 🔍 Semantic Search & Retrieval

Multi-faceted retrieval capabilities powered by:
- Elasticsearch vector search
- OpenAI embeddings (text-embedding-3)
- Cosine similarity scoring
- Metadata-aware filtering

Supports:
- Domain-scoped retrieval
- Global semantic querying
- Multi-document evidence collection
- Cross-domain relationship discovery

---

---

# Hybrid Embedding Architecture

A core innovation that improves semantic understanding and classification accuracy.

Instead of relying solely on document embeddings, the platform combines multiple semantic signals:

```python
hybrid_embedding = (metadata_embedding × 0.7) + (chunk_centroid_embedding × 0.3)
```

**Benefits:**
- **Richer Context:** Metadata contributes semantic signals about document focus
- **Improved Clustering:** Better semantic grouping within domains
- **Accurate Classification:** More precise domain assignment decisions
- **Enhanced Retrieval:** Higher relevance matching during queries

This weighted combination ensures both document content and structured metadata inform all downstream semantic operations.

---

# Adaptive Domain Centroid System

**Domains are not static containers—they are adaptive semantic entities that continuously evolve.**

## Semantic Foundation

Each domain begins with a semantic embedding generated from:
- Domain name
- Domain description

This provides an initial semantic anchor even when the domain contains no documents.

## Dynamic Centroid Evolution

As documents are assigned to a domain, the centroid is computed as:

```python
domain_centroid = average(all_hybrid_embeddings_in_domain)
```

This evolving centroid creates a **learned semantic representation** of the domain based on actual assigned content.

## Centroid Recomputation Triggers

Domain centroids are automatically recomputed when:

1. **Documents Added:** New documents increase the semantic representation
2. **Documents Deleted:** Removal adjusts the semantic center
3. **Documents Reassigned:** Moving documents between domains updates both source and target domain centroids

## Fallback to Semantic Foundation

If a domain contains no documents:
- The system falls back to the domain's original semantic embedding
- This preserves domain identity and enables retrieval even with empty domains
- As documents are added, the domain transitions to its learned centroid

## Impact on System Behavior

This adaptive approach creates:
- **Self-Improving Classification:** Domains become better classifiers as more documents are added
- **Semantic Learning:** The system learns "what this domain is about" through assigned documents
- **Dynamic Domain Discovery:** New semantic relationships emerge as the knowledge base grows
- **Robust Empty-Domain Handling:** Placeholder domains maintain semantic meaning until populated

---

---

# Adaptive Domain-Aware RAG Platform

Unlike traditional ReAct-style agents, this system implements an **adaptive retrieval-reasoning architecture** that treats domain understanding as a learned, evolving component.

## System Approach

Rather than purely agentic reasoning with tool use, the platform combines:
- **Domain-Aware Retrieval:** Intelligent routing using adaptive centroids
- **Hybrid Semantic Search:** Multi-signal ranking for precision
- **Grounded Reasoning:** LLM processing with explicit evidence grounding
- **Adaptive Learning:** Continuous refinement through document assignment

## Core Capabilities

The system can:
- **Retrieve Evidence:** Multi-document retrieval using domain-aware similarity
- **Compare Sources:** Analyze relationships between retrieved documents
- **Detect Contradictions:** Identify conflicting information across sources
- **Summarize Findings:** Synthesize evidence into coherent narratives
- **Generate Grounded Responses:** Produce answers with explicit source attribution

## Reasoning Design

Response generation is optimized to:
- Reduce hallucination through explicit evidence requirements
- Encourage analytical reasoning across multiple sources
- Force source attribution for all claims
- Support transparency in AI decision-making
- Enable auditable knowledge lineage

---

# Agent Architecture

## User Query Flow

```
User Query
    ↓
Query Embedding Generation
    ↓
Domain Relevance Scoring
    ↓
Adaptive Domain Centroid Comparison
    ↓
Top Domains Selected
```

User queries are embedded and compared against all adaptive domain centroids. The system identifies which domains contain semantically relevant information, enabling domain-scoped or global retrieval strategies.

## Retrieval Flow

```
Selected Domains
    ↓
Elasticsearch Vector Search
    ↓
Hybrid Embedding Matching
    ↓
Metadata Filtering
    ↓
Evidence Ranking by Similarity
    ↓
Retrieved Context Window
```

Multi-document retrieval prioritizes both semantic relevance and metadata-based filtering. Retrieved documents are ranked by cosine similarity to the query embedding.

## LLM Reasoning Flow

```
Retrieved Context + Query
    ↓
Evidence Analysis
    ↓
Source Comparison
    ↓
Contradiction Detection
    ↓
Synthesis & Reasoning
    ↓
Grounded Response Generation
    ↓
Attribution & Sourcing
```

The LLM receives retrieved context and performs structured reasoning with explicit source references. All claims are traced back to original documents.

## Domain-Aware Retrieval

**Key Innovation:** The system uses adaptive domain centroids to intelligently route queries:

- **Centroid Matching:** Query embeddings are compared against domain centroids
- **Domain Ranking:** Domains are ranked by cosine similarity
- **Scoped Retrieval:** Retrieved results are prioritized from high-matching domains
- **Cross-Domain Context:** Global queries can retrieve from multiple domains
- **Adaptive Precision:** As domains evolve, retrieval becomes more accurate

```python
domain_relevance = cosine_similarity(query_embedding, domain_centroid)
retrieved_documents = elasticsearch_search(
    query=query,
    filters={"domain": top_matching_domains},
    hybrid_embeddings=True
)
```

## Evidence Grounding

Every response component includes:
- **Source Documents:** References to specific retrieved documents
- **Metadata Context:** Relevant metadata supporting the answer
- **Chunk Citations:** Specific text snippets backing claims
- **Confidence Indicators:** Relevance scores for retrieved evidence
- **Domain Attribution:** Which domains contributed the evidence

This ensures responses are fully transparent and auditable.

---

---

# Technical Innovations

This platform introduces several technical advancements beyond traditional RAG systems:

## 🎯 Hybrid Embeddings
Combines metadata semantics (70%) and chunk content (30%) for richer representation and more accurate classification than content-only embeddings alone.

## 📊 Adaptive Domain Centroids
Domains learn and evolve through accumulated documents rather than remaining static. Centroids serve as semantic anchors that improve with each new assignment.

## 🎪 Domain-Aware Classification
Intelligent routing combines semantic similarity scoring with metadata-based filtering for precise domain assignment and multi-document retrieval.

## 📰 Automated News Expansion
Tavily integration enables continuous knowledge base growth through automated retrieval, processing, and domain-aware ingestion of external news content.

## 🔗 Multi-Document Reasoning
Rather than isolated Q&A, the system performs structured reasoning across multiple retrieved documents with explicit source attribution and contradiction detection.

---

# Frontend Features

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

# Document Lifecycle

The journey of a document through the system:

```
Upload (or News Retrieval)
    ↓
Text Extraction
    ↓
AI Metadata Extraction (title, keywords, entities, etc.)
    ↓
Chunking & Tokenization
    ↓
Hybrid Embedding Generation (metadata + content)
    ↓
Elasticsearch Indexing
    ↓
Domain Similarity Scoring
    ↓
Adaptive Domain Assignment (highest cosine similarity)
    ↓
Domain Centroid Update (average of all domain embeddings)
    ↓
Available for Semantic Retrieval
```

Each stage in this pipeline adds semantic richness and organizational context to the document.

---

# Domain Learning Mechanism

**Domains continuously learn and improve through document assignment.**

## Learning Process

1. **Initial State:** Domain begins with semantic embedding from name + description
2. **Document Assignment:** Documents are assigned based on highest similarity to domain centroid
3. **Centroid Evolution:** New document embedding is averaged into domain centroid
4. **Semantic Refinement:** Domain's semantic center shifts toward assigned document cluster
5. **Improved Classification:** Future documents are compared against this refined centroid
6. **Adaptive Precision:** Classification accuracy increases as domain matures

## Virtuous Cycle

```
More Documents Assigned
    ↓
More Refined Domain Centroid
    ↓
More Accurate Domain Boundary
    ↓
Better Subsequent Assignments
    ↓
Stronger Domain Identity
```

This creates a **self-reinforcing learning system** where each assignment improves the domain's ability to correctly classify future documents.

## Multi-Domain Dynamics

- Domains that receive similar documents converge toward shared semantic space
- Domains that receive diverse documents develop broader semantic understanding
- Document reassignment between domains provides explicit feedback signals
- The system discovers emergent relationships between domains through centroid analysis

---

# System Architecture

## High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Frontend Layer (React + Vite)                     │
│         Chat UI  ·  Upload  ·  Domains  ·  Metadata  ·  Repo         │
└────────────────────────────────┬─────────────────────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │                            │
         ┌──────────▼──────────┐      ┌──────────▼─────────┐
         │   FastAPI Backend   │      │   Tavily API       │
         │   (RAG Agent)       │      │  (News Retrieval)  │
         │                     │      │                    │
         │  • Ingestion        │      └────────────────────┘
         │  • Retrieval        │
         │  • Reasoning        │      ┌────────────────────┐
         │  • Domain Logic     │      │  OpenAI APIs       │
         │                     │      │  • Embeddings      │
         └──────────┬──────────┘      │  • GPT Models      │
                    │                 └────────────────────┘
         ┌──────────┼──────────┐
         │          │          │
    ┌────▼──┐   ┌───▼────┐ ┌──▼───────┐
    │ SQLite│   │Elastic │ │ Domain   │
    │Metadata   │Search  │ │ Similarity
    │ Store     │Vector  │ │ Layer &  │
    │           │Engine  │ │Centroids │
    └────────┘  └────────┘ └──────────┘
```

## Component Details

### Ingestion Pipeline
- **Input:** Documents (PDF, DOCX, TXT, MD) or News articles
- **Processing:** Text extraction → Metadata extraction → Embedding generation
- **Output:** Indexed documents in Elasticsearch with domain assignment

### Domain-Aware Retrieval Layer
- **Query Analysis:** Embed user query
- **Domain Scoring:** Compute similarity to all domain centroids
- **Retrieval Routing:** Retrieve from high-relevance domains
- **Result Ranking:** Rank by hybrid embedding similarity

### RAG Reasoning Engine
- **Context Assembly:** Combine retrieved documents with query
- **Evidence Analysis:** Process multiple sources for synthesis
- **Response Generation:** Create grounded answer with attribution

---
---

# Tech Stack

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
| Embeddings | OpenAI (text-embedding-3) |
| LLM | GPT-5.4 nano |
| News Retrieval | Tavily API |
| Document Parsing | pypdf, python-docx |
| Vector Operations | NumPy, Scikit-learn |

---

# Project Structure

```bash
Internproject2/
├── backend/
│   ├── routers/
│   │   ├── ingest.py                 # Document upload & ingestion
│   │   ├── query.py                  # RAG query endpoint
│   │   ├── news.py                   # News ingestion & trigger
│   │   └── documents.py              # Document CRUD & management
│   │
│   ├── services/
│   │   ├── document_ingestion_service.py      # Upload → indexing pipeline
│   │   ├── retrieval_service.py               # Query → document retrieval
│   │   ├── rag_agent_service.py               # Reasoning & response generation
│   │   ├── metadata_service.py                # Metadata storage & querying
│   │   ├── hybrid_embedding_service.py        # Metadata + content embeddings
│   │   ├── domain_similarity_service.py       # Domain cosine similarity
│   │   ├── domain_centroid_service.py         # Domain centroid computation
│   │   ├── domain_assignment_service.py       # Adaptive domain assignment
│   │   ├── news_ingestion_service.py          # Tavily + processing pipeline
│   │   ├── extraction_service.py              # LLM metadata extraction
│   │   ├── text_extraction_service.py         # Document → text conversion
│   │   └── vector_service.py                  # Elasticsearch operations
│   │
│   ├── prompts/
│   │   ├── domain_assignment_prompt.py        # Domain classification prompt
│   │   └── metadata_prompt.py                 # Metadata extraction prompt
│   │
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py              # Configuration & constants
│   │   │   └── paths.py               # File path management
│   │   ├── db/
│   │   │   └── database.py            # SQLite initialization
│   │   └── models/                    # Data models & schemas
│   │
│   ├── storage/
│   │   ├── uploads/                   # User-uploaded documents
│   │   ├── news_articles/             # Downloaded news content
│   │   └── outputs/                   # Generated artifacts
│   │
│   ├── main.py                        # FastAPI app entry point
│   ├── pyproject.toml                 # Dependencies & metadata
│   └── Dockerfile                     # Container configuration
│
└── frontend/
    ├── src/
    │   ├── components/                # React components
    │   │   ├── ChatWindow.jsx          # Main chat interface
    │   │   ├── SidebarFolders.jsx      # Domain navigation
    │   │   ├── UploadModal.jsx         # Document upload
    │   │   ├── MetadataModal.jsx       # Metadata editor
    │   │   └── DocumentRepository.jsx  # Document browser
    │   │
    │   ├── pages/                      # Page components
    │   ├── services/                   # API client services
    │   ├── App.jsx                     # Root component
    │   ├── main.jsx                    # React entry point
    │   ├── index.css                   # Global styles
    │   └── App.css                     # App-specific styles
    │
    ├── public/                         # Static assets
    ├── vite.config.js                  # Vite build configuration
    ├── package.json                    # Dependencies
    ├── Dockerfile                      # Container configuration
    └── README.md                       # Frontend documentation
```

---

# Detailed System Flow

## Document Ingestion to Retrieval

```
INGESTION PHASE
  ├─ User uploads document (PDF/DOCX/TXT/MD)
  ├─ Text extraction service converts to raw text
  ├─ Metadata extraction LLM identifies: title, keywords, entities, regions
  ├─ Chunking service splits text into semantic chunks
  ├─ Hybrid embedding service generates embeddings
  │  └─ (metadata_embedding × 0.7) + (chunk_centroid × 0.3)
  ├─ Elasticsearch indexes document with vectors
  ├─ Domain similarity service scores against all domain centroids
  ├─ Document assigned to highest-similarity domain
  └─ Domain centroid updated (recomputed as average of domain embeddings)

RETRIEVAL PHASE
  ├─ User submits query through chat interface
  ├─ Query embedding generated using same embedding model
  ├─ Domain similarity service scores query against all domain centroids
  ├─ Top-N domains identified based on similarity
  ├─ Elasticsearch vector search within selected domains
  ├─ Results ranked by hybrid embedding cosine similarity
  ├─ Retrieved documents assembled into context window
  └─ Context passed to RAG agent for reasoning

REASONING PHASE
  ├─ RAG agent receives query + retrieved context
  ├─ Agent performs structured analysis:
  │  ├─ Extracts key information from each source
  │  ├─ Compares and synthesizes across documents
  │  ├─ Detects contradictions or confirmation
  │  └─ Identifies source attribution
  ├─ LLM generates grounded response with citations
  ├─ Response includes metadata references and confidence scores
  └─ Response streamed to user with source visualization
```

---

# Deployment & Setup

## Prerequisites

- Python 3.11+
- Node.js 18+
- Elasticsearch 8.x instance
- OpenAI API key
- Tavily API key (for news ingestion)

## Environment Configuration

Create `.env` file in backend directory:

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
ELASTICSEARCH_URL=http://localhost:9200
DATABASE_URL=sqlite:///./knowledge_base.db
```

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker-compose up
```

This starts:
- FastAPI backend (port 8000)
- React frontend (port 5173)
- Elasticsearch (port 9200)

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Edit `backend/app/core/config.py` for:
- Embedding model selection
- Domain similarity threshold
- Hybrid embedding weights
- Chunking strategy
- News ingestion frequency

---

# Future Roadmap

## Planned Enhancements

- **Streaming Responses:** Real-time token streaming for improved UX
- **Caching Layer:** Redis integration for performance optimization
- **Kubernetes:** Production-grade container orchestration
- **Fine-Tuned Embeddings:** Domain-specific embedding models
- **Knowledge Graphs:** Entity relationship visualization
- **Scheduled Ingestion:** Automatic periodic news fetching
- **Multi-Agent Workflows:** Specialized agents for different query types
- **Authentication:** User management and role-based access control
- **Analytics Dashboard:** Query trends, domain statistics, performance metrics
- **Multi-Language Support:** Document processing in multiple languages

---

# Project Summary

## What Makes This Different

This platform demonstrates enterprise-grade AI engineering practices:

1. **Adaptive Learning:** Domains don't just organize—they learn and evolve
2. **Semantic Precision:** Hybrid embeddings and domain centroids improve over time
3. **Automated Expansion:** Real-time news integration keeps knowledge current
4. **Grounded Reasoning:** Multi-document synthesis with explicit source attribution
5. **Production-Ready:** Docker deployment, error handling, scalable architecture

## Suitable For

- **Internship Portfolio:** Demonstrates full-stack AI engineering
- **Enterprise Deployment:** Scalable, production-ready design patterns
- **GitHub Showcase:** Well-documented, architected system
- **Learning:** Comprehensive examples of RAG, embeddings, and semantic routing

---

# Conclusion

This Adaptive Domain-Aware RAG Platform showcases advanced knowledge management through:
- Semantic intelligence that improves over time
- Hybrid signal fusion for richer understanding
- Automated knowledge expansion from external sources
- Grounded, transparent AI reasoning
- Enterprise-grade architecture and deployment

The system moves beyond static document management to create a living knowledge system that learns, adapts, and serves increasingly relevant information as it grows.
