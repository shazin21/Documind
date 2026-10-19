import re
from typing import List, Set
from app.rag.types import ScoredPassage
from app.schemas.chat import Citation


class CitationService:
    """Verifies citations generated in LLM answers against verified retrieved passages."""

    def extract_and_verify_citations(
        self,
        answer: str,
        passages: List[ScoredPassage],
    ) -> List[Citation]:
        """
        Parses citation markers e.g. [1], [2], [1, 2] from answer text,
        verifies they map to valid retrieved passages, and extracts factual excerpts.
        """
        if not answer or not passages:
            return []

        normalized_answer = answer.replace("【", "[").replace("】", "]")
        # Find bracketed citation numbers: [1], [2], [1, 2]
        citation_tokens = re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", normalized_answer)
        cited_indices: Set[int] = set()

        for group in citation_tokens:
            for num_str in group.split(","):
                try:
                    idx = int(num_str.strip())
                    if 1 <= idx <= len(passages):
                        cited_indices.add(idx)
                except ValueError:
                    continue

        verified_citations: List[Citation] = []

        # Maintain citation order based on appearance
        for idx in sorted(cited_indices):
            passage = passages[idx - 1]
            # Extract clean, concise excerpt (first 2-3 sentences or first 250 characters)
            excerpt = self._extract_excerpt(passage.text)

            citation = Citation(
                citation_id=f"[{idx}]",
                document_id=passage.document_id,
                document_name=passage.document_name,
                page_number=passage.page_number,
                chunk_id=passage.chunk_id,
                excerpt=excerpt,
                score=passage.score,
            )
            verified_citations.append(citation)

        return verified_citations

    def _extract_excerpt(self, text: str, max_chars: int = 280) -> str:
        clean_text = " ".join(text.strip().split())
        if len(clean_text) <= max_chars:
            return clean_text
        # Cut at word boundary
        truncated = clean_text[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > 100:
            truncated = truncated[:last_space]
        return truncated + "..."


citation_service = CitationService()
