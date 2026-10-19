import uuid
from unittest.mock import patch
from app.db.models import Base
from app.schemas.evaluation import (
    BatchEvaluationResult,
    EvaluationMetricScores,
    EvaluationRunRequest,
    EvaluationSample,
    TestCase as EvalTestCase,
)
from app.services.evaluation_service import evaluation_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_evaluation_service_run_mock():
    # Setup in-memory sqlite test session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    try:
        test_case = EvalTestCase(
            id="test-1",
            question="What is the maximum carryover for annual leave?",
            expected_pages=[1],
            expected_answer="Up to 5 unused annual leave days may be carried forward.",
            has_sufficient_evidence=True,
        )

        request = EvaluationRunRequest(
            run_name="test_mock_run",
            retrieval_mode="dense",
            use_reranker=False,
            top_k=3,
            test_cases=[test_case],
        )

        run = evaluation_service.run_evaluation(db=db, request=request)

        assert run.id is not None
        assert run.run_name == "test_mock_run"
        assert run.total_cases == 1
        assert run.recall_at_k is not None
        assert run.mrr is not None
        assert run.faithfulness is not None
        assert run.answer_relevance is not None

        # Verify scores are bounded between 0 and 1
        assert 0.0 <= run.faithfulness <= 1.0
        assert 0.0 <= run.answer_relevance <= 1.0

        runs = evaluation_service.list_runs(db)
        assert len(runs) >= 1
        assert runs[0].run_name == "test_mock_run"

    finally:
        db.close()


def test_evaluate_samples_reusable_interface():
    samples = [
        EvaluationSample(
            question="How many days can be carried forward?",
            answer="Up to 5 days may be carried forward [1].",
            contexts=["Employees may carry forward up to 5 days into next year."],
            reference="5 days.",
        ),
        EvaluationSample(
            question="What is the secret vault code?",
            answer="Based on the provided documents, there is insufficient evidence to answer this question.",
            contexts=["No relevant information found."],
            reference="There is insufficient evidence.",
        ),
    ]

    result: BatchEvaluationResult = evaluation_service.evaluate_samples(samples)

    assert result.overall_faithfulness is not None
    assert result.overall_answer_relevance is not None
    assert len(result.sample_scores) == 2

    for score in result.sample_scores:
        assert isinstance(score, EvaluationMetricScores)
        assert score.faithfulness is not None
        assert 0.0 <= score.faithfulness <= 1.0
        assert score.answer_relevance is not None
        assert 0.0 <= score.answer_relevance <= 1.0


def test_evaluate_samples_empty_and_edge_cases():
    # Empty samples list
    empty_result = evaluation_service.evaluate_samples([])
    assert empty_result.overall_faithfulness is None
    assert empty_result.overall_answer_relevance is None
    assert len(empty_result.sample_scores) == 0

    # Sample with empty answer and empty contexts
    edge_sample = EvaluationSample(
        question="Empty test",
        answer="",
        contexts=[],
        reference=None,
    )
    edge_result = evaluation_service.evaluate_samples([edge_sample])
    assert len(edge_result.sample_scores) == 1
    assert edge_result.sample_scores[0].faithfulness == 0.0
    assert edge_result.sample_scores[0].answer_relevance == 0.0


def test_provider_error_graceful_fallback():
    samples = [
        EvaluationSample(
            question="Sample question?",
            answer="Sample answer with citation [1].",
            contexts=["Sample context."],
        )
    ]

    # Force an exception inside the RAGAS evaluation block
    with patch("app.core.config.settings.LLM_PROVIDER", "openai"):
        with patch("app.core.config.settings.OPENAI_API_KEY", "dummy_key"):
            with patch("ragas.evaluate", side_effect=RuntimeError("Provider connection timed out")):
                result = evaluation_service.evaluate_samples(samples)
                # Ensure the service does not crash and provides graceful fallback
                assert result.overall_faithfulness is not None
                assert result.overall_answer_relevance is not None
                assert len(result.sample_scores) == 1


def test_step_1_chunking_evaluation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    try:
        from app.db.models import Document, DocumentChunk

        doc_id = uuid.uuid4()
        doc = Document(
            id=doc_id,
            filename="test_policy.pdf",
            storage_path="uploads/test.pdf",
            file_size_bytes=1024,
            content_hash="abc123hash",
            page_count=2,
            processing_status="completed",
        )
        chunk1 = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc_id,
            chunk_index=0,
            page_number=1,
            chunk_text="Annual leave must be requested 2 weeks in advance." * 3,
        )
        chunk2 = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc_id,
            chunk_index=1,
            page_number=2,
            chunk_text="Fleet vehicles require maintenance every 10,000 miles." * 2,
        )
        db.add_all([doc, chunk1, chunk2])
        db.commit()

        eval_s1 = evaluation_service.evaluate_chunking(db, document_ids=[doc_id])
        assert eval_s1.total_chunks == 2
        assert eval_s1.total_pages == 2
        assert eval_s1.undersized_chunks == 0
        assert eval_s1.boundary_integrity_rate == 1.0
        assert eval_s1.step_score >= 0.70
        assert eval_s1.status == "PASSED"

    finally:
        db.close()


def test_step_2_retrieval_evaluation():
    from app.rag.types import ScoredPassage

    p1 = ScoredPassage(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_name="doc.pdf",
        page_number=1,
        text="Sample page 1 text",
        score=0.92,
        rank=1,
        source_retriever="hybrid",
    )
    p2 = ScoredPassage(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_name="doc.pdf",
        page_number=3,
        text="Sample page 3 text",
        score=0.75,
        rank=2,
        source_retriever="hybrid",
    )

    # Positive case where expected page is 1
    eval_pos = evaluation_service.evaluate_retrieval_step(
        query="What is page 1 content?",
        retrieved_passages=[p1, p2],
        expected_pages=[1],
        has_sufficient_evidence=True,
        latency_ms=12.5,
        retrieval_mode="hybrid",
        top_k=2,
    )
    assert eval_pos.hit is True
    assert eval_pos.reciprocal_rank == 1.0
    assert eval_pos.context_precision == 0.5
    assert eval_pos.top_score == 0.92
    assert eval_pos.status == "PASSED"

    # Negative case (out of domain)
    eval_neg = evaluation_service.evaluate_retrieval_step(
        query="What is Mars rover code?",
        retrieved_passages=[p1, p2],
        expected_pages=[],
        has_sufficient_evidence=False,
        latency_ms=8.0,
        retrieval_mode="hybrid",
        top_k=2,
    )
    assert eval_neg.hit is True
    assert eval_neg.reciprocal_rank == 1.0
    assert eval_neg.status == "PASSED"


def test_step_3_reranking_evaluation():
    from app.rag.types import ScoredPassage

    chunk_a = uuid.uuid4()
    chunk_b = uuid.uuid4()

    before = [
        ScoredPassage(chunk_id=chunk_a, document_id=uuid.uuid4(), document_name="doc.pdf", page_number=5, text="Doc 5", score=0.8, rank=1, source_retriever="hybrid"),
        ScoredPassage(chunk_id=chunk_b, document_id=uuid.uuid4(), document_name="doc.pdf", page_number=1, text="Doc 1", score=0.7, rank=2, source_retriever="hybrid"),
    ]
    # Reranking promotes chunk_b to rank 1
    after = [
        ScoredPassage(chunk_id=chunk_b, document_id=uuid.uuid4(), document_name="doc.pdf", page_number=1, text="Doc 1", score=1.5, rank=1, source_retriever="reranked"),
        ScoredPassage(chunk_id=chunk_a, document_id=uuid.uuid4(), document_name="doc.pdf", page_number=5, text="Doc 5", score=-0.2, rank=2, source_retriever="reranked"),
    ]

    eval_rerank = evaluation_service.evaluate_reranking_step(
        query="Annual leave policy",
        before_passages=before,
        after_passages=after,
        expected_pages=[1],
        enabled=True,
        latency_ms=15.0,
        top_k=2,
    )
    assert eval_rerank.enabled is True
    assert eval_rerank.top1_changed is True
    assert eval_rerank.top1_improved is True
    assert eval_rerank.score_separation is not None
    assert eval_rerank.status == "PASSED"
    assert eval_rerank.step_score == 1.0


def test_step_4_generation_evaluation():
    eval_gen = evaluation_service.evaluate_generation_step(
        query="What is the carryover?",
        answer="Employees may carry forward up to 5 days [1].",
        contexts=["Employees may carry forward up to 5 days into next calendar year."],
        citations=[{"citation_id": "1"}],
        expected_answer="5 days",
        expected_sufficient=True,
        insufficient_detected=False,
        latency_ms=250.0,
        faithfulness=1.0,
        answer_relevance=0.9,
    )
    assert eval_gen.citation_count == 1
    assert eval_gen.citation_validity == 1.0
    assert eval_gen.abstention_correctness == 1.0
    assert eval_gen.status == "PASSED"
    assert eval_gen.step_score >= 0.85


def test_evaluation_run_contains_multi_step_diagnostics():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    try:
        case = EvalTestCase(
            id="multi-1",
            question="What is the vehicle maintenance interval?",
            expected_pages=[2],
            expected_answer="Every 10,000 miles.",
            has_sufficient_evidence=True,
        )
        req = EvaluationRunRequest(
            run_name="multi_step_test_run",
            retrieval_mode="hybrid",
            use_reranker=False,
            top_k=3,
            test_cases=[case],
        )

        run = evaluation_service.run_evaluation(db, req)
        metrics = run.metrics_json

        # Verify all steps are evaluated and recorded
        assert "pipeline_summary" in metrics
        summary = metrics["pipeline_summary"]
        assert "step_1_chunking" in summary
        assert "step_2_retrieval" in summary
        assert "step_3_reranking" in summary
        assert "step_4_generation" in summary
        assert "composite_pipeline_index" in summary
        assert 0.0 <= summary["composite_pipeline_index"] <= 1.0

        assert "step_evaluations" in metrics
        assert len(metrics["step_evaluations"]) == 1
        case_step = metrics["step_evaluations"][0]
        assert "step_1_chunking" in case_step
        assert "step_2_retrieval" in case_step
        assert "step_3_reranking" in case_step
        assert "step_4_generation" in case_step
        assert "composite_pipeline_score" in case_step

    finally:
        db.close()

