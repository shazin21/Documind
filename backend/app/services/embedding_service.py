from typing import Any, Dict, List
from app.core.logging import logger
from app.providers.embeddings import BaseEmbeddingProvider, get_embedding_provider


class EmbeddingService:
    """Orchestrates embedding generation for chunks and user queries."""

    def __init__(self, provider: BaseEmbeddingProvider | None = None):
        self._provider = provider

    @property
    def provider(self) -> BaseEmbeddingProvider:
        if self._provider is None:
            self._provider = get_embedding_provider()
        return self._provider

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """Generates batch embeddings for a list of chunk dicts containing 'chunk_text'."""
        if not chunks:
            return []
        texts = [chunk["chunk_text"] for chunk in chunks]
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.provider.embed_documents(texts)
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generates a normalized embedding for a user question."""
        cleaned = query.strip()
        if not cleaned:
            raise ValueError("Query cannot be empty for embedding generation.")
        return self.provider.embed_query(cleaned)


embedding_service = EmbeddingService()
