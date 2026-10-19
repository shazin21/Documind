from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class EvaluationSample(BaseModel):
    """Single sample for RAGAS evaluation."""
    question: str
    answer: str
    contexts: List[str]
    reference: Optional[str] = None


class EvaluationMetricScores(BaseModel):
    """Scores for a single evaluated sample."""
    faithfulness: Optional[float] = None
    answer_relevance: Optional[float] = None


class BatchEvaluationResult(BaseModel):
    """Aggregated and per-sample results from evaluation."""
    overall_faithfulness: Optional[float] = None
    overall_answer_relevance: Optional[float] = None
    sample_scores: List[EvaluationMetricScores] = Field(default_factory=list)



class TestCase(BaseModel):
    id: Optional[str] = None
    question: str
    document_ids: Optional[List[UUID]] = None
    document_filenames: Optional[List[str]] = None
    expected_pages: List[int] = Field(default_factory=list)
    expected_answer: Optional[str] = None
    has_sufficient_evidence: bool = True


class EvaluationRunRequest(BaseModel):
    run_name: str = Field(..., min_length=1, max_length=128)
    retrieval_mode: str = Field("hybrid", description="'hybrid', 'dense', or 'keyword'")
    use_reranker: bool = False
    top_k: int = Field(5, ge=1, le=20)
    test_cases: Optional[List[TestCase]] = None


class StepChunkingEvaluation(BaseModel):
    """Step 1 Evaluation: Text extraction and chunking quality."""
    total_pages: int = 0
    pages_with_text: int = 0
    total_chunks: int = 0
    avg_chunk_length: float = 0.0
    min_chunk_length: int = 0
    max_chunk_length: int = 0
    chunk_length_std: float = 0.0
    undersized_chunks: int = 0
    boundary_integrity_rate: float = 1.0
    step_score: float = 1.0
    status: str = "PASSED"  # PASSED, DEGRADED


class StepRetrievalEvaluation(BaseModel):
    """Step 2 Evaluation: Candidate passage retrieval quality."""
    retrieval_mode: str = "hybrid"
    top_k: int = 5
    hit: bool = False
    reciprocal_rank: float = 0.0
    context_precision: float = 0.0
    top_score: Optional[float] = None
    score_spread: Optional[float] = None
    latency_ms: float = 0.0
    step_score: float = 0.0
    status: str = "PASSED"  # PASSED, FAILED


class StepRerankingEvaluation(BaseModel):
    """Step 3 Evaluation: Cross-Encoder reranking impact and shift."""
    enabled: bool = False
    initial_candidate_count: int = 0
    top_k: int = 5
    rank_displacement_sum: int = 0
    top1_changed: bool = False
    top1_improved: bool = False
    score_separation: Optional[float] = None
    latency_ms: float = 0.0
    step_score: float = 1.0
    status: str = "PASSED"  # PASSED, SKIPPED, DEGRADED


class StepGenerationEvaluation(BaseModel):
    """Step 4 Evaluation: Groundedness, Faithfulness, Relevancy, Citations, and Abstention."""
    faithfulness: Optional[float] = None
    answer_relevance: Optional[float] = None
    citation_count: int = 0
    citation_coverage: float = 0.0
    citation_validity: float = 1.0
    insufficient_evidence_detected: bool = False
    abstention_correctness: float = 1.0
    latency_ms: float = 0.0
    step_score: float = 0.0
    status: str = "PASSED"  # PASSED, FAILED


class MultiStepCaseEvaluation(BaseModel):
    """Holistic multi-step evaluation for a single pipeline query."""
    case_id: Optional[str] = None
    question: str
    expected_pages: List[int] = Field(default_factory=list)
    expected_sufficient: bool = True
    step_1_chunking: Optional[StepChunkingEvaluation] = None
    step_2_retrieval: StepRetrievalEvaluation
    step_3_reranking: StepRerankingEvaluation
    step_4_generation: StepGenerationEvaluation
    composite_pipeline_score: float = 0.0
    total_latency_ms: float = 0.0
    all_steps_passed: bool = False


class TestCaseResult(BaseModel):
    question: str
    retrieved_pages: List[int]
    expected_pages: List[int]
    hit: bool
    reciprocal_rank: float
    insufficient_evidence_detected: bool
    expected_sufficient: bool
    latency_ms: float
    faithfulness: Optional[float] = None
    answer_relevance: Optional[float] = None
    step_evaluations: Optional[MultiStepCaseEvaluation] = None
    error: Optional[str] = None


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_name: str
    retrieval_mode: str
    recall_at_k: float
    mrr: float
    faithfulness: Optional[float] = None
    answer_relevance: Optional[float] = None
    total_cases: int
    passed_cases: int
    metrics_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

