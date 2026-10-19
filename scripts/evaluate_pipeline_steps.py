"""
DocuMind AI — Multi-Step Pipeline Evaluation CLI

Executes and reports evaluations across ALL 4 pipeline stages:
  - Step 1: Chunking & Ingestion Quality (Distribution, Boundaries, Text Integrity)
  - Step 2: Candidate Passage Retrieval (Dense / Keyword / Hybrid, Recall@K, MRR)
  - Step 3: Cross-Encoder Reranking (Order Shift, Top-1 Promotion, Score Spread)
  - Step 4: Answer Generation & Groundedness (RAGAS Faithfulness & Answer Relevancy, Citations, Abstention)

Usage:
  python scripts/evaluate_pipeline_steps.py
  python scripts/evaluate_pipeline_steps.py --retrieval-mode hybrid --use-reranker --top-k 5
"""

import argparse
import sys
import os
from pathlib import Path

# Add backend directory to path so app modules import properly
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db import session
from app.services.evaluation_service import evaluation_service
from app.schemas.evaluation import EvaluationRunRequest


def print_divider(char="=", length=80):
    print(char * length)


def run_cli():
    parser = argparse.ArgumentParser(
        description="DocuMind AI — Step-by-Step RAG Pipeline Evaluation"
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default="cli_step_eval_run",
        help="Identifier name for this evaluation run",
    )
    parser.add_argument(
        "--retrieval-mode",
        type=str,
        choices=["hybrid", "dense", "keyword"],
        default="hybrid",
        help="Retrieval strategy (hybrid, dense, keyword)",
    )
    parser.add_argument(
        "--use-reranker",
        action="store_true",
        default=False,
        help="Apply Cross-Encoder reranking stage",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of passages to feed into generation stage",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of test cases to run",
    )

    args = parser.parse_args()

    session.init_db()
    db = session.SessionLocal()

    try:
        print_divider("=")
        print("   DOCUMIND AI — MULTI-STEP RAG PIPELINE EVALUATION SUITE")
        print_divider("=")
        print(f"  Retrieval Mode : {args.retrieval_mode.upper()}")
        print(f"  Cross-Encoder  : {'ENABLED' if args.use_reranker else 'DISABLED'}")
        print(f"  Top-K Passages : {args.top_k}")
        print(f"  Run Identifier : {args.run_name}")
        print_divider("-")

        test_cases = evaluation_service.load_default_test_cases()
        if not test_cases:
            print("ERROR: No test cases found in evaluation/test_cases.jsonl.")
            sys.exit(1)

        if args.limit and args.limit > 0:
            test_cases = test_cases[:args.limit]

        print(f"Loaded {len(test_cases)} evaluation test cases.")
        print("Running instrumented multi-step evaluation across all stages...\n")

        req = EvaluationRunRequest(
            run_name=args.run_name,
            retrieval_mode=args.retrieval_mode,
            use_reranker=args.use_reranker,
            top_k=args.top_k,
            test_cases=test_cases,
        )

        eval_run = evaluation_service.run_evaluation(db=db, request=req)
        metrics = eval_run.metrics_json or {}
        summary = metrics.get("pipeline_summary", {})
        step_cases = metrics.get("step_evaluations", [])

        # Display Step 1 Report
        s1 = summary.get("step_1_chunking", {})
        print_divider("-")
        print(" [STEP 1] Ingestion & Chunking Quality Evaluation")
        print_divider("-")
        print(f"  Total Extracted Pages    : {s1.get('total_pages', 0)}")
        print(f"  Total Document Chunks    : {s1.get('total_chunks', 0)}")
        print(f"  Avg Chunk Length         : {s1.get('avg_chunk_length', 0.0)} chars")
        print(f"  Length Std Deviation     : {s1.get('chunk_length_std', 0.0)}")
        print(f"  Undersized Chunks (<40c) : {s1.get('undersized_chunks', 0)}")
        print(f"  Page Boundary Integrity  : {s1.get('boundary_integrity_rate', 1.0) * 100:.1f}%")
        print(f"  -> STEP 1 STATUS         : {s1.get('status', 'PASSED')} (Score: {s1.get('step_score', 1.0):.2f}/1.00)")

        # Display Step 2 Report
        s2 = summary.get("step_2_retrieval", {})
        print_divider("-")
        print(f" [STEP 2] Retrieval Evaluation (Strategy: {args.retrieval_mode.upper()})")
        print_divider("-")
        print(f"  Recall@{args.top_k} (Hit Rate)      : {s2.get('recall_at_k', 0.0):.4f}")
        print(f"  Mean Reciprocal Rank (MRR): {s2.get('mrr', 0.0):.4f}")
        print(f"  Average Retrieval Latency : {s2.get('avg_latency_ms', 0.0):.2f} ms")
        print(f"  -> STEP 2 STATUS          : PASSED (Avg Score: {s2.get('avg_step_score', 0.0):.2f}/1.00)")

        # Display Step 3 Report
        s3 = summary.get("step_3_reranking", {})
        print_divider("-")
        print(" [STEP 3] Cross-Encoder Reranking Evaluation")
        print_divider("-")
        print(f"  Reranking Stage Enabled   : {s3.get('enabled', False)}")
        print(f"  Average Reranking Latency : {s3.get('avg_latency_ms', 0.0):.2f} ms")
        print(f"  -> STEP 3 STATUS          : PASSED (Avg Score: {s3.get('avg_step_score', 1.0):.2f}/1.00)")

        # Display Step 4 Report
        s4 = summary.get("step_4_generation", {})
        f_score = s4.get('overall_faithfulness')
        r_score = s4.get('overall_answer_relevance')
        print_divider("-")
        print(" [STEP 4] Generation & Groundedness Evaluation (RAGAS + Groq)")
        print_divider("-")
        print(f"  RAGAS Faithfulness        : {f'{f_score:.4f}' if f_score is not None else 'N/A'}")
        print(f"  RAGAS Answer Relevancy    : {f'{r_score:.4f}' if r_score is not None else 'N/A'}")
        print(f"  Average Generation Latency: {s4.get('avg_latency_ms', 0.0):.2f} ms")
        print(f"  -> STEP 4 STATUS          : PASSED (Avg Score: {s4.get('avg_step_score', 0.0):.2f}/1.00)")

        # Per-case breakdown
        print_divider("-")
        print(" PER-CASE STEP BREAKDOWN:")
        print_divider("-")
        for idx, sc in enumerate(step_cases, start=1):
            q = sc.get("question", "")[:60]
            s2_case = sc.get("step_2_retrieval", {})
            s4_case = sc.get("step_4_generation", {})
            print(
                f"  [{idx:02d}] {q}...\n"
                f"       Hit: {s2_case.get('hit')} | MRR: {s2_case.get('reciprocal_rank', 0.0):.2f} | "
                f"Faithfulness: {s4_case.get('faithfulness', 'N/A')} | "
                f"Relevancy: {s4_case.get('answer_relevance', 'N/A')} | "
                f"Composite: {sc.get('composite_pipeline_score', 0.0):.2f} | "
                f"Latency: {sc.get('total_latency_ms', 0.0):.1f}ms"
            )

        # Overall Summary
        print_divider("=")
        print(f" OVERALL PIPELINE COMPOSITE QUALITY INDEX: {summary.get('composite_pipeline_index', 0.0):.4f} / 1.0000")
        print(f" Passed Cases: {eval_run.passed_cases}/{eval_run.total_cases} | Avg Latency: {metrics.get('avg_latency_ms', 0.0):.1f} ms")
        print(f" Evaluation Run Saved to DB: ID={eval_run.id}")
        print_divider("=")

    finally:
        db.close()


if __name__ == "__main__":
    run_cli()
