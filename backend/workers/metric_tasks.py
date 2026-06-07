"""
Celery Background Workers — AutoAB

Tasks:
  1. compute_metric_snapshots  — runs every 5 min, aggregates events → MetricSnapshot
  2. check_experiment_completion — runs every 15 min, auto-stops expired experiments
"""

from celery import Celery
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "autoab",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "compute-metrics-every-5min": {
        "task":     "workers.metric_tasks.compute_metric_snapshots",
        "schedule": 300.0,   # every 5 minutes
    },
    "check-experiment-completion-every-15min": {
        "task":     "workers.metric_tasks.check_experiment_completion",
        "schedule": 900.0,   # every 15 minutes
    },
}
celery_app.conf.timezone = "UTC"


def _get_db():
    """Synchronous DB session for Celery workers."""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    engine  = create_engine(settings.sync_database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


# ── Task 1: Compute Metric Snapshots ─────────────────────────
@celery_app.task(name="workers.metric_tasks.compute_metric_snapshots")
def compute_metric_snapshots():
    """
    Aggregate all raw events per experiment per group → write MetricSnapshot.
    Called every 5 minutes. Powers the live dashboard charts.
    """
    from sqlalchemy import select
    from models import Experiment, Event, MetricSnapshot, ExperimentStatus
    from datetime import datetime

    db = _get_db()
    try:
        running_exps = db.execute(
            select(Experiment).where(Experiment.status == ExperimentStatus.RUNNING)
        ).scalars().all()

        snapshots_written = 0
        for exp in running_exps:
            for group in ["control", "treatment"]:
                events = db.execute(
                    select(Event).where(
                        Event.experiment_id == exp.id,
                        Event.group == group,
                    )
                ).scalars().all()

                if not events:
                    continue

                # ── Aggregate ─────────────────────────────────
                sessions    = {e.session_id for e in events}
                conversions = {e.session_id for e in events if e.event_type == "conversion"}
                clicks      = {e.session_id for e in events if e.event_type == "click"}

                revenues  = [e.value    for e in events if e.event_type == "conversion" and e.value is not None]
                durations = [e.duration for e in events if e.event_type == "session_end" and e.duration is not None]
                scrolls   = [e.scroll_depth for e in events if e.scroll_depth is not None]

                n_users = len(sessions)
                n_conv  = len(conversions)
                n_click = len(clicks)

                snap = MetricSnapshot(
                    experiment_id        = exp.id,
                    group                = group,
                    snapshot_at          = datetime.utcnow(),
                    users_count          = n_users,
                    sessions_count       = n_users,
                    conversions          = n_conv,
                    conversion_rate      = n_conv  / n_users if n_users else 0.0,
                    total_revenue        = sum(revenues),
                    avg_revenue          = sum(revenues) / len(revenues) if revenues else 0.0,
                    ctr                  = n_click / n_users if n_users else 0.0,
                    avg_session_duration = sum(durations) / len(durations) if durations else 0.0,
                    bounce_rate          = len([s for s in sessions if s not in clicks]) / n_users if n_users else 0.0,
                    avg_scroll_depth     = sum(scrolls)  / len(scrolls)  if scrolls  else 0.0,
                )
                db.add(snap)
                snapshots_written += 1

        db.commit()
        return f"✅ Snapshots written: {snapshots_written} (for {len(running_exps)} running experiments)"

    except Exception as e:
        db.rollback()
        return f"❌ Error: {e}"
    finally:
        db.close()


# ── Task 2: Auto-Stop Expired Experiments ────────────────────
@celery_app.task(name="workers.metric_tasks.check_experiment_completion")
def check_experiment_completion():
    """
    Check if any running experiment has exceeded its duration_days.
    Auto-transitions them from RUNNING → ANALYSIS.
    """
    from sqlalchemy import select
    from models import Experiment, ExperimentStatus
    from datetime import datetime

    db = _get_db()
    try:
        running = db.execute(
            select(Experiment).where(Experiment.status == ExperimentStatus.RUNNING)
        ).scalars().all()

        auto_stopped = []
        for exp in running:
            if exp.start_time:
                elapsed_days = (
                    datetime.utcnow() - exp.start_time.replace(tzinfo=None)
                ).total_seconds() / 86_400

                if elapsed_days >= exp.duration_days:
                    exp.status   = ExperimentStatus.ANALYSIS
                    exp.end_time = datetime.utcnow()
                    auto_stopped.append(str(exp.id))

        db.commit()
        return f"✅ Auto-stopped {len(auto_stopped)} experiments: {auto_stopped}"

    except Exception as e:
        db.rollback()
        return f"❌ Error: {e}"
    finally:
        db.close()
