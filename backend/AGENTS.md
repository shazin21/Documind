# Backend Guidelines & Architecture — DocuMind AI

## 1. FastAPI Architecture & Principles
- **Framework**: FastAPI with Python 3.11+.
- **Data Validation**: Strict Pydantic v2 schemas for request and response models.
- **Modularity**: Clean separation of concerns:
  - `api/routes/`: Thin HTTP route handlers doing validation, dependency injection, and error mapping.
  - `core/`: Application settings (Pydantic Settings), structured logging, and security utilities.
  - `db/`: SQLAlchemy 2.x declarative models, session factory, and repository patterns.
  - `services/`: Core business logic (PDF processing, text chunking, embedding generation, retrieval, reranking, grounded generation).
  - `providers/`: Swappable LLM adapters (Gemini, OpenAI, Mock) and embedding models.
  - `rag/`: Prompt construction, injection defense, evidence assembly, and citation verification.

## 2. Directory Structure
```
backend/
├── app/
│   ├── main.py                # FastAPI app initialization, CORS, and route registration
│   ├── api/
│   │   ├── deps.py            # Dependency injection (db session, services)
│   │   └── routes/
│   │       ├── health.py      # /health endpoint
│   │       ├── documents.py   # /api/v1/documents (upload, list, get, delete, pages)
│   │       ├── chat.py        # /api/v1/chat, /api/v1/conversations
│   │       └── evaluation.py  # /api/v1/evaluation (runs, metrics, datasets)
│   ├── core/
│   │   ├── config.py          # Settings loaded from environment variables
│   │   ├── logging.py         # Structured logging configuration
│   │   └── security.py        # Safe filename sanitization, secret handling
│   ├── db/
│   │   ├── session.py         # SQLAlchemy engine and sessionmaker
│   │   ├── models.py          # Document, DocumentChunk, Conversation, Message, EvaluationRun
│   │   └── repositories/      # DocumentRepository, ChunkRepository, ConversationRepository
│   ├── schemas/
│   │   ├── document.py        # DocumentUploadResponse, DocumentResponse, PageResponse
│   │   ├── chat.py            # ChatRequest, ChatResponse, Citation, EvidenceExcerpt
│   │   └── evaluation.py      # EvaluationRunRequest, EvaluationRunResponse, MetricScore
│   ├── services/
│   │   ├── pdf_service.py     # PDF validation, PyMuPDF page text extraction, metadata
│   │   ├── chunking_service.py# Recursive character chunking preserving paragraph boundaries
│   │   ├── embedding_service.py # Sentence-transformers batch embedding (all-MiniLM-L6-v2)
│   │   ├── retrieval_service.py # Hybrid search (pgvector + full-text search) & RRF
│   │   ├── reranking_service.py # Optional cross-encoder reranking
│   │   ├── generation_service.py# Grounded prompt execution and LLM communication
│   │   ├── citation_service.py# Citation validation and claim-to-evidence alignment
│   │   └── evaluation_service.py# Evaluation runner computing Recall@K, MRR, Faithfulness
│   ├── providers/
│   │   ├── embeddings.py      # Embedding provider interface & SentenceTransformers implementation
│   │   └── llm.py             # LLM provider interface (Gemini, OpenAI, Mock)
│   └── rag/
│       ├── pipeline.py        # End-to-end RAG pipeline coordination
│       ├── prompts.py         # Grounded prompt templates with prompt injection boundary markers
│       └── types.py           # Internal RAG data structures (CandidateChunk, ScoredResult)
└── tests/                     # Automated pytest test cases
```

## 3. Database & pgvector Conventions
- Vector dimension is configured as **384** (matching `sentence-transformers/all-MiniLM-L6-v2`).
- Both vector distance (cosine distance via `<=>` operator) and full-text search (`to_tsvector('english', chunk_text)`) are indexed and utilized in hybrid queries.
- Reciprocal Rank Fusion (RRF) combines dense and sparse ranks with standard constant $k = 60$.
- In local environments where PostgreSQL is not yet started, the repository layer must cleanly report configuration status or operate safely.

## 4. Ingestion & RAG Pipeline Rules
1. **File Validation**: Validate size ($\le 20$ MB), `.pdf` extension, and `%PDF-` header.
2. **Page Text Preservation**: Retain exact original page numbers (1-indexed) with extracted text.
3. **Chunking**: Chunk sizes default to 1000 characters with 150 overlap. Never index empty chunks.
4. **Grounded Generation**: The model must never invent source document IDs or page numbers. Citations must match verified retrieval chunks.
5. **Insufficient Evidence**: When similarity or keyword scores fall below relevance thresholds, explicitly answer with an insufficient evidence notice.

## 5. Development & Testing Commands
```powershell
# Run backend server
.\backend\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend

# Run automated tests
.\backend\.venv\Scripts\pytest backend/tests -v
```
