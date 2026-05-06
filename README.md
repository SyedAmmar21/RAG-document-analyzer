# AI-Powered RAG Document Assistant

## Project Overview

AI-Powered RAG Document Assistant is a full-stack web application that allows users to upload documents and interact with them using AI-powered question answering.

The system uses a Retrieval-Augmented Generation (RAG) architecture with Elasticsearch vector search and LLM integration to provide context-aware answers based on uploaded documents.

---

# Features

* Upload and process documents
* Repository management system
* AI-powered document question answering
* Elasticsearch semantic search
* RAG-based retrieval pipeline
* React frontend with FastAPI backend
* SQLite metadata storage

---

# Architecture

```text
React Frontend
       ↓
FastAPI Backend
       ↓
Document Processing Pipeline
       ↓
Embedding Generation
       ↓
Elasticsearch Vector Database
       ↓
RAG Retrieval + LLM Response
```

---

# Tech Stack

## Frontend

* React
* JavaScript
* CSS

## Backend

* FastAPI
* Python
* Uvicorn

## AI / RAG

* LangChain
* LLM APIs
* Embedding Models

## Database

* SQLite
* Elasticsearch

---

# Project Structure

```text
project-root/
│
├── backend/
│   ├── routers/
│   ├── services/
│   └── main.py
│
├── frontend/
│   ├── src/
│   └── App.jsx
│
├── uploads/
└── README.md
```

---

# Setup Steps

## 1. Clone Repository

```bash
git clone <repository-url>
cd <project-folder>
```

## 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

## 4. Elasticsearch

Ensure Elasticsearch is running:

```text
http://localhost:9200
```

---

# API Endpoints

```http
POST   /ingest
GET    /documents
DELETE /documents/{id}
POST   /query
```

---

# Conclusion

This project demonstrates a complete AI-powered RAG web application with document ingestion, semantic retrieval, vector search, and AI-assisted question answering using a scalable full-stack architecture.
