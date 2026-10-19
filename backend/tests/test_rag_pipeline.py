import uuid
from app.providers.llm import MockLLMProvider
from app.rag.types import ScoredPassage
from app.services.generation_service import GenerationService


def test_grounded_generation_with_citations():
    mock_llm = MockLLMProvider()
    service = GenerationService(llm_provider=mock_llm)

    doc_id = uuid.uuid4()
    passages = [
        ScoredPassage(
            chunk_id=uuid.uuid4(),
            document_id=doc_id,
            document_name="Policy.pdf",
            page_number=4,
            text="Department managers approve annual leave requests within 48 hours.",
            score=0.95,
            rank=1,
        )
    ]

    result = service.generate_grounded_answer(
        question="Who approves annual leave requests?",
        passages=passages,
    )

    assert not result.insufficient_evidence
    assert "[1]" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].page_number == 4
    assert result.citations[0].document_name == "Policy.pdf"


def test_insufficient_evidence_when_no_passages():
    mock_llm = MockLLMProvider()
    service = GenerationService(llm_provider=mock_llm)

    result = service.generate_grounded_answer(
        question="What is the nuclear launch code?",
        passages=[],
    )

    assert result.insufficient_evidence
    assert "insufficient evidence" in result.answer.lower()
    assert len(result.citations) == 0


def test_insufficient_evidence_when_information_not_in_passages():
    mock_llm = MockLLMProvider()
    service = GenerationService(llm_provider=mock_llm)

    passages = [
        ScoredPassage(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            document_name="Cooking.pdf",
            page_number=1,
            text="Add two cups of flour and stir the dough slowly.",
            score=0.3,
            rank=1,
        )
    ]

    result = service.generate_grounded_answer(
        question="What is the speed limit on Mars?",
        passages=passages,
    )

    assert result.insufficient_evidence
    assert "insufficient evidence" in result.answer.lower()
