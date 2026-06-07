from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models import Experiment, Event, MetricSnapshot
from services.stats_engine import ABTestAnalyser, calculate_sample_size, compute_current_power

router = APIRouter(prefix="/analysis", tags=["analysis"])


async def _get_analysis_results(experiment_id: str, db: AsyncSession) -> dict:
    """Internal helper — fetches latest snapshots and runs all statistical tests."""
    snapshots = {}
    for group in ["control", "treatment"]:
        result = await db.execute(
            select(MetricSnapshot)
            .where(
                MetricSnapshot.experiment_id == experiment_id,
                MetricSnapshot.group == group,
            )
            .order_by(MetricSnapshot.snapshot_at.desc())
            .limit(1)
        )
        snap = result.scalar_one_or_none()
        if snap:
            snapshots[group] = snap

    if len(snapshots) < 2:
        return {"message": "Not enough data yet. Need events from both groups.", "results": {}}

    analyser = ABTestAnalyser(
        ctrl_snapshot=snapshots["control"],
        trt_snapshot=snapshots["treatment"],
        alpha=0.05,
    )
    return analyser.run_all_tests()


@router.get("/{experiment_id}/results")
async def get_results(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Run full statistical analysis on current experiment data."""
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    analysis = await _get_analysis_results(experiment_id, db)
    return {
        "experiment_id": experiment_id,
        "experiment_name": exp.name,
        "status": exp.status,
        "llm_diff": exp.llm_diff,
        "llm_report": exp.llm_report,
        **analysis,
    }


@router.get("/{experiment_id}/snapshots")
async def get_snapshots(
    experiment_id: str,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
):
    """
    Return time-series metric snapshots for chart rendering.
    The React dashboard polls this every 30 seconds.
    """
    result = await db.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.experiment_id == experiment_id)
        .order_by(MetricSnapshot.snapshot_at.asc())
        .limit(limit)
    )
    snapshots = result.scalars().all()

    return [
        {
            "group":                 s.group,
            "snapshot_at":           s.snapshot_at.isoformat(),
            "users_count":           s.users_count,
            "conversions":           s.conversions,
            "conversion_rate":       s.conversion_rate,
            "ctr":                   s.ctr,
            "avg_revenue":           s.avg_revenue,
            "avg_session_duration":  s.avg_session_duration,
            "bounce_rate":           s.bounce_rate,
            "avg_scroll_depth":      s.avg_scroll_depth,
        }
        for s in snapshots
    ]


@router.get("/{experiment_id}/power")
async def get_power(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return current statistical power and sample size progress.
    Used to render the power meter and progress bar on the dashboard.
    """
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    ctrl_count_r = await db.execute(
        select(func.count(Event.session_id.distinct()))
        .where(
            Event.experiment_id == str(experiment_id),
            Event.group == "control",
        )
    )
    trt_count_r = await db.execute(
        select(func.count(Event.session_id.distinct()))
        .where(
            Event.experiment_id == str(experiment_id),
            Event.group == "treatment",
        )
    )

    n_ctrl = ctrl_count_r.scalar() or 0
    n_trt  = trt_count_r.scalar() or 0

    return compute_current_power(
        n_control=n_ctrl,
        n_treatment=n_trt,
        mde=exp.min_detectable_effect,
        alpha=exp.alpha,
        required_n=exp.required_sample_size or 0,
    )


@router.get("/{experiment_id}/segments")
async def get_segments(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """
    Break down conversion rate by device type for both groups.
    Detects Simpson's Paradox — where overall result hides segment-level harm.
    """
    result = await db.execute(
        select(
            Event.group,
            Event.device,
            func.count(Event.session_id.distinct()).label("users"),
            func.count(
                Event.session_id.distinct()
            ).filter(Event.event_type == "conversion").label("conversions"),
        )
        .where(Event.experiment_id == experiment_id)
        .group_by(Event.group, Event.device)
    )
    rows = result.all()

    segments = {}
    for row in rows:
        key = f"{row.group}_{row.device or 'unknown'}"
        conv_rate = row.conversions / row.users if row.users > 0 else 0
        segments[key] = {
            "group":           row.group,
            "device":          row.device or "unknown",
            "users":           row.users,
            "conversions":     row.conversions,
            "conversion_rate": round(conv_rate, 4),
        }

    return {"segments": segments}
