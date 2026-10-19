# DocuMind AI — Agent Guidelines & Repository Architecture

## 1. Project Overview & Architectural Principles

DocuMind AI is an advanced PDF knowledge retrieval and question-answering system. The application adheres to production-grade engineering principles:
- **Correctness & Groundedness**: Every answer must be derived directly from retrieved passages, with verified page citations and excerpts. If insufficient evidence exists, the system must explicitly state so rather than hallucinate.
- **Explainability**: Passage selection, rank fusion scores, and retrieval sources must be transparent and inspectable.
- **Security & Privacy**: Strict input validation, safe file handling, bounded context limits, prompt injection defenses, and separation of credentials.
- **Maintainability & Type Safety**: Strict TypeScript on the frontend (Next.js App Router) and strict Pydantic v2 schemas on the backend (FastAPI + SQLAlchemy 2.x).
- **No Fabricated Data**: Never invent benchmarks, streaming illusions, mock citations, or false test passes. Always report real observed outputs.

---

## 2. Repository Structure

```
DocuMind AI/
├── AGENTS.md                  # Root agent instructions and conventions
├── README.md                  # Project overview, setup, and walkthrough
├── .gitignore                 # Monorepo git ignore rules
├── .env.example               # Template environment configuration (placeholders only)
├── docker-compose.yml         # PostgreSQL 16 + pgvector container
├── frontend/                  # Next.js 16 (App Router, Tailwind CSS, TypeScript)
│   ├── AGENTS.md              # Frontend-specific guidelines and conventions
│   ├── app/                   # Next.js App Router pages (/, /documents, /chat)
│   ├── components/            # UI, chat, document, pdf-viewer, citations components
│   ├── lib/                   # Typed API client, utility functions
│   ├── types/                 # Shared TypeScript interfaces
│   └── package.json
└── backend/                   # FastAPI backend (Python 3.11)
    ├── AGENTS.md              # Backend-specific guidelines and conventions
    ├── app/
    │   ├── main.py            # FastAPI entrypoint and lifespan management
    │   ├── api/routes/        # Modular API routes (health, documents, chat, evaluation)
    │   ├── core/              # Config (pydantic-settings), logging, security
    │   ├── db/                # SQLAlchemy session, engine, models, and repositories
    │   ├── schemas/           # Pydantic v2 request/response schemas
    │   ├── services/          # PDF extraction, chunking, embedding, retrieval, reranking, generation
    │   ├── providers/         # Interchangeable LLM and embedding adapters
    │   └── rag/               # Pipeline orchestrator, system prompts, verification
    ├── tests/                 # Pytest automated test suite
    └── pyproject.toml / requirements.txt
```

---

## 3. Development and Testing Commands

### Root & Database
- Start PostgreSQL + pgvector:
  ```powershell
  docker compose up -d
  ```
- Stop PostgreSQL:
  ```powershell
  docker compose down
  ```

### Backend (Python 3.11)
- Activate Virtual Environment:
  ```powershell
  .\backend\.venv\Scripts\Activate.ps1
  ```
- Run Backend Dev Server:
  ```powershell
  .\backend\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
  ```
- Run Backend Tests:
  ```powershell
  .\backend\.venv\Scripts\pytest backend/tests -v
  ```

### Frontend (Next.js 16)
- Install Dependencies:
  ```powershell
  cd frontend; npm install
  ```
- Run Frontend Dev Server:
  ```powershell
  cd frontend; npm run dev
  ```
- Run Frontend Build / Lint:
  ```powershell
  cd frontend; npm run lint
  cd frontend; npm run build
  ```

---

## 4. Coding Conventions

- **Inspect Before Changing**: Inspect existing working implementations before refactoring. Do not delete working modules or replace them with empty placeholders.
- **Python**: Type annotations on all functions. Use Pydantic v2 schemas for all external boundaries. Preserve existing docstrings and comments.
- **TypeScript**: Strict mode enabled. Use Zod schemas to validate API responses. Maintain consistent component styling via Tailwind CSS and shadcn/ui patterns.
- **Error Handling**: Return structured HTTP exceptions with informative detail fields. Avoid unhandled 500 errors.

---

## 5. Security & Safety Rules

- Never commit secrets, passwords, or live API keys to version control.
- Validate all incoming files: check file size (max 20 MB), file extension (`.pdf`), and `%PDF-` magic byte headers.
- Never write uploaded files with untrusted user filenames; use opaque server-generated UUIDs.
- Isolate retrieved document text as untrusted content inside prompts to prevent prompt injection.

---

## 6. Definition of Done

A task is complete only when:
1. Code passes all linting, type checks, and automated tests.
2. Changes are verified with real, observed tool output (no fabricated passes).
3. Documentation and AGENTS.md files reflect the current state of the implementation.
