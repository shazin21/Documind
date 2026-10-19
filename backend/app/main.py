from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat, documents, evaluation, health
from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database schemas on startup."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL_NAME} ({settings.EMBEDDING_DIMENSION}d)")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    init_db()
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="DocuMind AI — Grounded PDF knowledge retrieval, question answering, and evaluation system.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(evaluation.router)

# Legacy compatibility alias for existing prototype endpoint: POST /documents/upload
app.add_api_route(
    "/documents/upload",
    documents.upload_document,
    methods=["POST"],
    include_in_schema=False,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
