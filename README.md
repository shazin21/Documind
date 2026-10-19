# DocuMind AI — Advanced PDF Knowledge Retrieval & Grounded Q&A

DocuMind AI is a production-minded, portfolio-grade PDF knowledge retrieval and question-answering system. It implements a complete, deterministic Retrieval-Augmented Generation (RAG) architecture engineered with strict factual groundedness, hybrid dense-sparse search, pgvector persistence, verifiable page-level citations, and reproducible benchmark evaluations.

---

## Key System Features

- **Multi-Document Ingestion & Validation**: Safe file upload, magic header validation (`%PDF-`), page-by-page text extraction via PyMuPDF, and scanned document OCR requirement detection.
- **Recursive Paragraph Chunking**: Semantic character chunking with configurable overlap (`CHUNK_SIZE=1000`, `CHUNK_OVERLAP=150`) preserving document IDs and 1-indexed page metadata.
- **Hybrid Search with Reciprocal Rank Fusion (RRF)**: Combines dense vector similarity search (`sentence-transformers/all-MiniLM-L6-v2`, 384d normalized vectors in pgvector) and PostgreSQL full-text keyword search (`to_tsvector` and `websearch_to_tsquery`) using standard RRF ($k = 60$).
- **Optional Cross-Encoder Reranking**: Re-scores top candidate passages using a cross-encoder model for high precision on complex multi-passage questions.
- **Grounded Answer Generation & Injection Defense**: Untrusted document text is isolated within strict boundary markers `<retrieved_passages>`. System prompts strictly prohibit speculation or document-embedded instruction overrides.
- **Claim-to-Evidence Citations**: Every assertion is cited with interactive badges (`[1]`, `[2]`) that open the cited page directly in the PDF viewer with excerpt preview.
- **Explicit Insufficient-Evidence Abstention**: When relevant evidence is missing from the corpus or similarity scores fall below confidence thresholds, the system explicitly refuses to guess.
- **Reproducible Evaluation Dashboard**: Measures Recall@K, Mean Reciprocal Rank (MRR), Faithfulness, and negative test case abstention against verifiable test datasets.

---

## Repository Architecture

```
DocuMind AI/
├── AGENTS.md                  # Root agent instructions and conventions
├── README.md                  # Comprehensive documentation and walkthrough
├── .gitignore                 # Monorepo git ignore rules
├── .env.example               # Template environment configuration (placeholders only)
├── docker-compose.yml         # PostgreSQL 16 + pgvector container
├── scripts/
│   └── init_db.sql            # Database schema and extension initialization
├── evaluation/
│   ├── README.md              # Evaluation methodology and benchmark guide
│   ├── test_cases.jsonl       # Active benchmark test cases
│   └── test_cases.example.jsonl # Template evaluation dataset
├── frontend/                  # Next.js 16 (App Router, React 19, Tailwind CSS 4)
│   ├── AGENTS.md              # Frontend architecture guidelines
│   ├── app/
│   │   ├── layout.tsx         # App layout with navigation & theme
│   │   ├── page.tsx           # Dashboard view with stats & quick upload
│   │   ├── documents/page.tsx # Document Library (upload, status, delete)
│   │   ├── chat/page.tsx      # Grounded Q&A workspace with document selector
│   │   └── evaluation/page.tsx# Benchmark runner and metrics visualization
│   ├── components/            # Reusable UI, chat, documents, and PDF viewer components
│   ├── lib/                   # Typed API client and utility helpers
│   └── types/                 # Shared TypeScript interfaces
└── backend/                   # FastAPI backend (Python 3.11)
    ├── AGENTS.md              # Backend architecture guidelines
    ├── requirements.txt       # Frozen pinned dependencies
    ├── main.py                # Root backend entrypoint
    ├── app/
    │   ├── main.py            # FastAPI application with CORS and lifespan
    │   ├── api/routes/        # Modular API routes (health, documents, chat, evaluation)
    │   ├── core/              # Config (pydantic-settings), logging, security
    │   ├── db/                # SQLAlchemy models and repository layer
    │   ├── schemas/           # Pydantic v2 request/response schemas
    │   ├── services/          # PDF, chunking, embedding, retrieval, reranking, generation
    │   ├── providers/         # Swappable LLM (Mock, Gemini, OpenAI) and Embedding adapters
    │   └── rag/               # Pipeline orchestrator, system prompts, verification
    └── tests/                 # Pytest test suite (11 automated test cases)
```

---

## Local Setup & Development (Windows / PowerShell)

### Prerequisites

1. **Python 3.11+**: Verified with virtual environment at `backend/.venv/`.
2. **Node.js v20+ & npm**: Verified with Node v24.19.0.
3. **Docker Desktop** (Optional for local PostgreSQL + pgvector container).

---

### Step 1: Environment Configuration

Copy the template `.env.example` to `.env` in the project root:

```powershell
Copy-Item .env.example .env
```

Key environment options in `.env`:
- `LLM_PROVIDER`: Set to `mock` (default for offline, zero-cost deterministic tests), `gemini`, or `openai`.
- `GEMINI_API_KEY`: Required when `LLM_PROVIDER=gemini`.
- `OPENAI_API_KEY`: Required when `LLM_PROVIDER=openai`.
- `DATABASE_URL`: `postgresql+psycopg://documind:documind_secret@localhost:5432/documind_db`.

---

### Step 2: Database Initialization (Docker Compose)

Start PostgreSQL 16 with the `pgvector` extension:

```powershell
docker compose up -d
```

To verify the container is running and healthy:
```powershell
docker compose ps
```

---

### Step 3: Run Backend Development Server

Activate the Python virtual environment and start FastAPI on port 8000:

```powershell
# In PowerShell:
.\backend\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```

The interactive OpenAPI documentation will be accessible at:
[http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 4: Run Frontend Development Server

In a second terminal, start the Next.js development server:

```powershell
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Verification & Testing

### Running Backend Unit & Integration Tests

Execute the comprehensive pytest test suite:

```powershell
.\backend\.venv\Scripts\pytest backend/tests -v
```

Tests verify:
- Health check and database readiness
- Safe PDF validation, size bounds, and opaque storage
- PyMuPDF page-by-page text extraction and metadata preservation
- Paragraph-aligned text chunking with metadata tracking
- SentenceTransformers embedding dimensions (384d)
- Citation extraction, excerpt validation, and claim alignment
- Grounded generation with `MockLLMProvider`
- Insufficient evidence detection and negative case abstention

### Running Frontend Validation

Verify TypeScript types and build output:

```powershell
cd frontend
npm run lint
npm run build
```

---

## End-to-End Walkthrough

1. **Upload Document**: Navigate to `/documents` or the Dashboard upload dropzone. Drop a PDF document (e.g., an employee handbook or technical specification).
2. **Indexing Observation**: Observe document status change from `queued` $\rightarrow$ `processing` $\rightarrow$ `completed`. Chunks and 384d normalized embeddings are persisted.
3. **Ask Grounded Questions**: Navigate to `/chat`. Filter by the document or search across the corpus. Ask a factual question.
4. **Citation Inspection**: In the assistant response, click any citation badge (`[1]`, `[2]`). The PDF Viewer opens side by side, navigating directly to that cited page with verbatim excerpt highlighting.
5. **Abstention Test**: Ask a question whose answer is absent from the uploaded document (e.g., *"What is the password to the vault?"*). Observe the amber callout confirming that the system accurately refused to hallucinate.
6. **Benchmark Evaluation**: Navigate to `/evaluation`. Click **Run Evaluation** to run the 5 ground-truth test cases and measure real Recall@K and MRR metrics.
