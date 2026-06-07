from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from database import get_db
from models import Event

router = APIRouter(prefix="/events", tags=["events"])


# ── Pydantic Schemas ──────────────────────────────────────────
class EventPayload(BaseModel):
    experiment_id: str
    session_id:    str
    group:         str            # "control" | "treatment"
    event_type:    str            # page_view | click | scroll | conversion | session_end
    element_id:    Optional[str]  = None
    page_url:      Optional[str]  = None
    value:         Optional[float] = None    # Revenue on conversion
    duration:      Optional[float] = None    # Session duration in seconds
    scroll_depth:  Optional[float] = None    # 0–100%
    device:        Optional[str]  = None     # mobile | desktop | tablet
    country:       Optional[str]  = None
    referrer:      Optional[str]  = None
    metadata:      Optional[dict] = None
    timestamp:     Optional[datetime] = None


class BatchEventPayload(BaseModel):
    events: List[EventPayload]


# ── Endpoints ─────────────────────────────────────────────────
@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_batch(
    payload: BatchEventPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive a batch of events from the JS SDK.
    The SDK flushes every 5 seconds — this is the primary ingestion endpoint.
    """
    db_events = [
        Event(
            id=uuid.uuid4(),
            experiment_id=e.experiment_id,
            session_id=e.session_id,
            group=e.group,
            event_type=e.event_type,
            element_id=e.element_id,
            page_url=e.page_url,
            value=e.value,
            duration=e.duration,
            scroll_depth=e.scroll_depth,
            device=e.device,
            country=e.country,
            referrer=e.referrer,
            metadata=e.metadata,
            timestamp=e.timestamp or datetime.utcnow(),
        )
        for e in payload.events
    ]
    db.add_all(db_events)
    await db.commit()
    return {"accepted": len(db_events)}


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def ingest_single(
    payload: EventPayload,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single event (convenience wrapper around /batch)."""
    return await ingest_batch(BatchEventPayload(events=[payload]), db)
