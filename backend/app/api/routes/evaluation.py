from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/api/v1/evaluation", tags=["Evaluation"])


@router.get(
    "/runs",
    response_model=List[EvaluationRunResponse],
    summary="List past evaluation runs",
)
def list_evaluation_runs(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return evaluation_service.list_runs(db, limit=limit)


@router.post(
    "/runs",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an evaluation run across test cases",
)
def trigger_evaluation_run(
    request: EvaluationRunRequest,
    db: Session = Depends(get_db),
):
    try:
        run = evaluation_service.run_evaluation(db, request)
        return run
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {str(e)}",
        )


@router.get(
    "/runs/{run_id}",
    response_model=EvaluationRunResponse,
    summary="Get details of a specific evaluation run",
)
def get_evaluation_run(
    run_id: str,
    db: Session = Depends(get_db),
):
    import uuid
    try:
        u_id = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID: {run_id}",
        )
    run = evaluation_service.get_run(db, u_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found",
        )
    return run


@router.get(
    "/runs/{run_id}/steps",
    summary="Get full step-by-step pipeline evaluation diagnostics for a run",
)
def get_evaluation_run_steps(
    run_id: str,
    db: Session = Depends(get_db),
):
    import uuid
    try:
        u_id = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID: {run_id}",
        )
    run = evaluation_service.get_run(db, u_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found",
        )
    metrics = run.metrics_json or {}
    return {
        "run_id": str(run.id),
        "run_name": run.run_name,
        "pipeline_summary": metrics.get("pipeline_summary", {}),
        "step_evaluations": metrics.get("step_evaluations", []),
    }

