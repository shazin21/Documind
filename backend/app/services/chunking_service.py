from typing import Any, Dict, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.core.logging import logger


class ChunkingService:
    """Chunks extracted page texts into overlapping, semantic segments while preserving metadata."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
            keep_separator=True,
            length_function=len,
        )

    def chunk_pages(
        self,
        pages_data: List[Dict[str, Any]],
        min_chunk_length: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Splits page text into numbered chunks.
        pages_data is expected to be a list of {'page': int, 'text': str}.
        Returns list of dicts:
        {
            'chunk_index': int,
            'page_number': int,
            'chunk_text': str,
            'char_length': int,
            'metadata': dict
        }
        """
        chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for page in pages_data:
            page_num = page.get("page", 1)
            page_text = page.get("text", "").strip()

            if not page_text or len(page_text) < min_chunk_length:
                continue

            split_texts = self.splitter.split_text(page_text)

            for local_idx, chunk_text in enumerate(split_texts):
                cleaned = chunk_text.strip()
                if len(cleaned) < min_chunk_length:
                    continue

                chunk_entry = {
                    "chunk_index": global_chunk_idx,
                    "page_number": page_num,
                    "chunk_text": cleaned,
                    "char_length": len(cleaned),
                    "metadata": {
                        "page_number": page_num,
                        "page_chunk_index": local_idx,
                        "global_chunk_index": global_chunk_idx,
                        "char_count": len(cleaned),
                    },
                }
                chunks.append(chunk_entry)
                global_chunk_idx += 1

        logger.info(f"Chunked {len(pages_data)} pages into {len(chunks)} text chunks.")
        return chunks


chunking_service = ChunkingService()
