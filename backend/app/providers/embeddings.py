from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass


class SentenceTransformersProvider(BaseEmbeddingProvider):
    """Local embedding generation using HuggingFace / SentenceTransformers."""

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        expected_dim: int = settings.EMBEDDING_DIMENSION,
    ):
        self.model_name = model_name
        self._expected_dim = expected_dim
        self._model = None

    def _get_model(self):
        if self._model is None:
            logger.info(f"Loading SentenceTransformers model: {self.model_name}...")
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            # Verify embedding dimension
            test_emb = self._model.encode(["dimension test"], normalize_embeddings=True)
            actual_dim = test_emb.shape[1]
            if actual_dim != self._expected_dim:
                raise ValueError(
                    f"Embedding dimension mismatch: model '{self.model_name}' produces "
                    f"{actual_dim} dimensions, but settings specify {self._expected_dim}."
                )
            logger.info(f"SentenceTransformers model loaded. Dimension: {actual_dim}")
        return self._model

    @property
    def dimension(self) -> int:
        return self._expected_dim

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        vec = model.encode([text], normalize_embeddings=True)[0]
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        vecs = model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vecs.tolist()


def get_embedding_provider() -> BaseEmbeddingProvider:
    return SentenceTransformersProvider()
