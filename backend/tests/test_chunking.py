from app.services.chunking_service import ChunkingService


def test_chunking_preserves_page_numbers_and_metadata():
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    pages = [
        {
            "page": 1,
            "text": "First page text. This is paragraph one. This is paragraph two with more information.",
        },
        {
            "page": 2,
            "text": "Second page text. This section discusses security and governance policies.",
        },
    ]

    chunks = service.chunk_pages(pages, min_chunk_length=10)

    assert len(chunks) >= 2
    # Verify page numbers match
    page_1_chunks = [c for c in chunks if c["page_number"] == 1]
    page_2_chunks = [c for c in chunks if c["page_number"] == 2]

    assert len(page_1_chunks) > 0
    assert len(page_2_chunks) > 0

    # Verify chunk indexing
    for i, c in enumerate(chunks):
        assert c["chunk_index"] == i
        assert "metadata" in c
        assert c["metadata"]["page_number"] == c["page_number"]


def test_empty_or_short_chunks_ignored():
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    pages = [
        {"page": 1, "text": "   "},
        {"page": 2, "text": "Hi"},  # Less than min_chunk_length (10)
    ]

    chunks = service.chunk_pages(pages, min_chunk_length=10)
    assert len(chunks) == 0
