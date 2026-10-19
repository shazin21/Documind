import uuid
from app.rag.types import ScoredPassage
from app.services.citation_service import CitationService


def test_extract_and_verify_citations():
    service = CitationService()
    doc_id = uuid.uuid4()
    chunk1_id = uuid.uuid4()
    chunk2_id = uuid.uuid4()

    passages = [
        ScoredPassage(
            chunk_id=chunk1_id,
            document_id=doc_id,
            document_name="Handbook.pdf",
            page_number=3,
            text="Employees receive 20 days of paid annual leave per calendar year.",
            score=0.92,
            rank=1,
        ),
        ScoredPassage(
            chunk_id=chunk2_id,
            document_id=doc_id,
            document_name="Handbook.pdf",
            page_number=5,
            text="Unused annual leave up to 5 days can be carried forward.",
            score=0.88,
            rank=2,
        ),
    ]

    answer = "Employees are entitled to 20 days of annual leave [1] and can carry forward up to 5 unused days [2]."
    citations = service.extract_and_verify_citations(answer, passages)

    assert len(citations) == 2
    assert citations[0].citation_id == "[1]"
    assert citations[0].page_number == 3
    assert "20 days of paid annual leave" in citations[0].excerpt
    assert citations[1].citation_id == "[2]"
    assert citations[1].page_number == 5


def test_invalid_citation_indices_ignored():
    service = CitationService()
    passages = [
        ScoredPassage(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            document_name="Doc.pdf",
            page_number=1,
            text="Single passage text.",
            score=0.9,
            rank=1,
        )
    ]

    # [99] does not exist in passages
    answer = "This refers to nonexistent passage [99]."
    citations = service.extract_and_verify_citations(answer, passages)
    assert len(citations) == 0
