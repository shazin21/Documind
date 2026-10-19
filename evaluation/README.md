# DocuMind AI — Evaluation Dataset & Methodology

## 1. Overview

DocuMind AI evaluates retrieval quality and generation accuracy using a reproducible dataset of test cases formatted as JSON Lines (`.jsonl`).

Each test case contains:
- `id`: Unique identifier for the test case.
- `question`: The natural language query.
- `expected_pages`: List of 1-indexed document page numbers that contain supporting evidence.
- `expected_answer`: Reference answer for comparison.
- `has_sufficient_evidence`: Boolean flag indicating whether the question can be answered from the corpus (`true`), or represents an out-of-domain negative test case requiring abstention (`false`).

---

## 2. Multi-Step Measured Metrics

DocuMind AI evaluates every stage of the pipeline independently and in composite:

### Step 1: Ingestion & Chunking Quality
- Total chunk count and extraction completeness.
- Chunk length distribution (mean, standard deviation, bounds).
- Undersized / degenerate chunk ratio.
- Page boundary integrity (1-indexed page preserving accuracy).

### Step 2: Candidate Passage Retrieval Quality
- **Recall@K (Hit Rate)**: Whether at least one expected evidence page was present in top-K retrieved passages.
- **Mean Reciprocal Rank (MRR)**: $1 / \text{rank}$ of the first ground-truth matching chunk.
- **Context Precision**: Ratio of candidate passages matching expected target pages.
- Candidate score distribution and retrieval latency.

### Step 3: Cross-Encoder Reranking
- Rank displacement sum: Total displacement in candidate order caused by cross-encoder rescoring.
- Top-1 promotion: Whether reranking promoted a ground-truth chunk into rank #1.
- Cross-encoder confidence gap & score separation.

### Step 4: Generation, Groundedness & Faithfulness
- **RAGAS Faithfulness**: Measures whether claims in the generated answer are grounded in retrieved context chunks (using Groq LLM + SentenceTransformers).
- **RAGAS Answer Relevancy**: Measures how directly the generated answer addresses the query.
- **Citation Quality & Validity**: Bracketed citation coverage and index validity.
- **Abstention Accuracy**: Explicit detection of insufficient evidence on negative / unanswerable test cases.

---

## 3. Running an Evaluation

### Via CLI (Recommended for Development & CI/CD):
```powershell
python scripts/evaluate_pipeline_steps.py --retrieval-mode hybrid --use-reranker --top-k 5
```

### Via Backend API:
```bash
# Trigger an evaluation run:
curl -X POST http://localhost:8000/api/v1/evaluation/runs \
  -H "Content-Type: application/json" \
  -d '{"run_name": "benchmark_v1", "retrieval_mode": "hybrid", "use_reranker": true, "top_k": 5}'

# View run history:
curl http://localhost:8000/api/v1/evaluation/runs

# View step-by-step pipeline diagnostics for a run:
curl http://localhost:8000/api/v1/evaluation/runs/<run_id>/steps
```

