from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.rag.types import ScoredPassage


class RerankingService:
    """Optional Cross-Encoder reranker to rescore candidate passages."""

    def __init__(self, model_name: str = settings.RERANKER_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._load_failed = False

    def _get_model(self):
        if self._model is None and not self._load_failed:
            try:
                from sentence_transformers import CrossEncoder

                logger.info(f"Loading CrossEncoder model: {self.model_name}...")
                self._model = CrossEncoder(self.model_name)
                logger.info("CrossEncoder loaded successfully.")
            except Exception as e:
                logger.warning(
                    f"Could not load CrossEncoder reranker '{self.model_name}': {e}. "
                    "Falling back to initial retrieval ranking."
                )
                self._load_failed = True
        return self._model

    def rerank(
        self,
        query: str,
        passages: List[ScoredPassage],
        top_k: int = 5,
    ) -> List[ScoredPassage]:
        """Scores (query, passage) pairs and returns top_k passages sorted by reranker score."""
        if not passages or top_k <= 0:
            return []

        model = self._get_model()
        if model is None:
            # Fall back to incoming ranking
            return passages[:top_k]

        pairs = [[query, p.text] for p in passages]
        try:
            scores = model.predict(pairs)
            scored_passages = []
            for i, p in enumerate(passages):
                score = float(scores[i])
                scored_passages.append(
                    ScoredPassage(
                        chunk_id=p.chunk_id,
                        document_id=p.document_id,
                        document_name=p.document_name,
                        page_number=p.page_number,
                        text=p.text,
                        score=round(score, 4),
                        rank=1,
                        source_retriever="reranked",
                        metadata=p.metadata,
                    )
                )

            # Sort descending by score
            scored_passages.sort(key=lambda p: p.score, reverse=True)
            for rank, p in enumerate(scored_passages[:top_k], start=1):
                p.rank = rank

            return scored_passages[:top_k]
        except Exception as e:
            logger.warning(f"Error during reranking: {e}. Falling back to baseline ranking.")
            return passages[:top_k]


reranking_service = RerankingService()
