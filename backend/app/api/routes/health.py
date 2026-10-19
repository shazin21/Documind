from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_database_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Health check endpoint reporting application and database connectivity status."""
    db_ok, db_msg = check_database_connection()

    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "connected": db_ok,
            "message": db_msg,
        },
        "embedding_model": {
            "name": settings.EMBEDDING_MODEL_NAME,
            "dimension": settings.EMBEDDING_DIMENSION,
        },
        "llm_provider": settings.LLM_PROVIDER,
    }
