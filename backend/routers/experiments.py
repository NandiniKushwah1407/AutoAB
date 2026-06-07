from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from database import get_db
from models import Experiment, ExperimentStatus
from services.stats_engine import calculate_sample_size
from services.llm_diff import analyse_diff_with_llm
from services.llm_report import generate_report

router = APIRouter(prefix="/experiments", tags=["experiments"])


# ── Pydantic Schemas ──────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    url_a: str
    url_b: str


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    url_a: str
    url_b: str
    primary_metric: str = "conversion_rate"
    alpha: float = 0.05
    min_detectable_effect: float = 0.02
    traffic_split: float = 0.5
    duration_days: float = 7.0


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    primary_metric: Optional[str] = None
    selected_metrics: Optional[list[str]] = None
    alpha: Optional[float] = None
    min_detectable_effect: Optional[float] = None
    duration_days: Optional[float] = None


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    url_a: str
    url_b: str
    status: str
    primary_metric: str
    alpha: float
    min_detectable_effect: float
    duration_days: float
    required_sample_size: Optional[float]
    created_at: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    llm_diff: Optional[dict]
    llm_report: Optional[dict]

    class Config:
        from_attributes = True


# ── Helper: run LLM diff in background ───────────────────────
async def _run_llm_diff(experiment_id: str, url_a: str, url_b: str, db: AsyncSession):
    try:
        diff_result = await analyse_diff_with_llm(url_a, url_b)
        result = await db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        exp = result.scalar_one_or_none()
        if exp:
            exp.llm_diff = diff_result
            await db.commit()
    except Exception as e:
        print(f"[LLM Diff Error] {e}")


# ── Endpoints ──────────────────────────────────────────────────
@router.post("/analyze")
async def analyze_changes(payload: AnalyzeRequest):
    """Analyze differences between two URLs without creating an experiment."""
    try:
        diff_result = await analyse_diff_with_llm(payload.url_a, payload.url_b)
        return {
            "success": True,
            "analysis": diff_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    payload: ExperimentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new experiment. LLM diff analysis starts in the background."""
    required_n = calculate_sample_size(
        baseline_rate=0.10,
        mde=payload.min_detectable_effect,
        alpha=payload.alpha,
    )
    exp = Experiment(
        id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        url_a=payload.url_a,
        url_b=payload.url_b,
        primary_metric=payload.primary_metric,
        alpha=payload.alpha,
        min_detectable_effect=payload.min_detectable_effect,
        traffic_split=payload.traffic_split,
        duration_days=payload.duration_days,
        required_sample_size=required_n,
        status=ExperimentStatus.DRAFT,
    )
    db.add(exp)
    await db.commit()
    await db.refresh(exp)

    # Kick off LLM diff analysis in background (non-blocking)
    background_tasks.add_task(
        _run_llm_diff, str(exp.id), payload.url_a, payload.url_b, db
    )
    return exp


@router.get("/", response_model=list[ExperimentResponse])
async def list_experiments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Experiment).order_by(Experiment.created_at.desc())
    )
    return result.scalars().all()

@router.patch("/{experiment_id}")
async def update_experiment(
    experiment_id: str, 
    payload: ExperimentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update experiment details before starting."""
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.status != ExperimentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only update draft experiments")

    # Update fields if provided
    if payload.name is not None:
        exp.name = payload.name
    if payload.description is not None:
        exp.description = payload.description
    if payload.primary_metric is not None:
        exp.primary_metric = payload.primary_metric
    if payload.alpha is not None:
        exp.alpha = payload.alpha
    if payload.min_detectable_effect is not None:
        exp.min_detectable_effect = payload.min_detectable_effect
    if payload.duration_days is not None:
        exp.duration_days = payload.duration_days
    
    # Store selected metrics if provided (could add to database model later)
    if payload.selected_metrics is not None:
        if not hasattr(exp, 'selected_metrics'):
            exp.llm_diff = exp.llm_diff or {}
            exp.llm_diff['selected_metrics'] = payload.selected_metrics
    
    await db.commit()
    await db.refresh(exp)
    return exp


@router.post("/{experiment_id}/start")
async def start_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.status not in [ExperimentStatus.DRAFT, ExperimentStatus.STOPPED]:
        raise HTTPException(status_code=400, detail=f"Cannot start experiment in status '{exp.status}'")

    exp.status     = ExperimentStatus.RUNNING
    exp.start_time = datetime.utcnow()
    await db.commit()
    await db.refresh(exp)
    return exp
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.status not in [ExperimentStatus.DRAFT, ExperimentStatus.STOPPED]:
        raise HTTPException(status_code=400, detail=f"Cannot start experiment in status '{exp.status}'")

    exp.status     = ExperimentStatus.RUNNING
    exp.start_time = datetime.utcnow()
    await db.commit()
    return {"message": "Experiment started", "id": str(exp.id), "status": "running"}


@router.post("/{experiment_id}/stop")
async def stop_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    exp.status   = ExperimentStatus.STOPPED
    exp.end_time = datetime.utcnow()
    await db.commit()
    return {"message": "Experiment stopped", "id": str(exp.id)}


@router.post("/{experiment_id}/generate-report")
async def generate_experiment_report(
    experiment_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger LLM report generation for a completed experiment."""
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    async def _run_report():
        from routers.analysis import _get_analysis_results
        analysis = await _get_analysis_results(experiment_id, db)
        report   = await generate_report(exp, analysis, exp.llm_diff or {})
        exp.llm_report = report
        exp.status     = ExperimentStatus.COMPLETED
        await db.commit()

    background_tasks.add_task(_run_report)
    return {"message": "Report generation started. Check back in ~30 seconds."}


@router.delete("/{experiment_id}", status_code=204)
async def delete_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    await db.delete(exp)
    await db.commit()
