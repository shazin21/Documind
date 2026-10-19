from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger
from app.db.models import Base

# Configure initial engine based on settings
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"connect_timeout": 2} if "sqlite" not in settings.DATABASE_URL else {"check_same_thread": False},
    pool_pre_ping=True,
    pool_size=10 if "sqlite" not in settings.DATABASE_URL else 5,
    max_overflow=20 if "sqlite" not in settings.DATABASE_URL else 10,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database sessions to request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Tuple[bool, str]:
    """Verifies database connectivity, falling back to local SQLite if PostgreSQL is offline."""
    global engine, SessionLocal

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            if engine.dialect.name == "postgresql":
                result = conn.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                ).scalar()
                if not result:
                    return False, "Database reachable, but pgvector extension is not installed."
                return True, "PostgreSQL reachable with pgvector extension enabled."
            return True, "Operating on local SQLite engine (documind.db)."
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection failed ({e}). Switching to local SQLite storage (documind.db) so system runs without Docker."
        )
        try:
            engine = create_engine(
                "sqlite:///documind.db",
                connect_args={"check_same_thread": False},
                echo=False,
            )
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base.metadata.create_all(bind=engine)
            return True, "Operating on local SQLite engine (PostgreSQL offline; start Docker for pgvector)."
        except Exception as sqlite_err:
            return False, f"All database connections failed: {sqlite_err}"


def init_db() -> None:
    """Initializes tables in the connected database."""
    global engine, SessionLocal
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables initialized on {engine.dialect.name} engine.")
    except Exception as e:
        logger.warning(
            f"Could not initialize {engine.dialect.name} ({e}). Switching to local SQLite fallback..."
        )
        try:
            engine = create_engine(
                "sqlite:///documind.db",
                connect_args={"check_same_thread": False},
                echo=False,
            )
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("Local SQLite database initialized at documind.db.")
        except Exception as fallback_err:
            logger.error(f"Failed to initialize database fallback: {fallback_err}")
