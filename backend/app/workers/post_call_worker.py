import asyncio
import json
import logging
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.services.queue import get_queue_service
from app.services.sentiment import get_sentiment_analyzer
from app.services.summary import get_summary_generator
from app.services.scoring import get_scoring_engine
from app.services.billing import record_usage

logger = logging.getLogger(__name__)


async def analyze_call_by_id(db: Session, call: models.Call) -> None:
    if not call.transcript:
        return

    sentiment_service = get_sentiment_analyzer()
    summary_service = get_summary_generator()
    scoring_service = get_scoring_engine()

    sentiment_result = sentiment_service.analyze_text(call.transcript)
    call.sentiment = sentiment_result["sentiment"]
    call.sentiment_score = sentiment_result["score"]

    summary_result = await summary_service.generate_summary(call.transcript)
    call.summary = summary_result["summary"]
    call.detected_intent = summary_result["customer_intent"]
    call.keywords = json.dumps(summary_result["key_points"])

    score_result = scoring_service.score_call(
        transcript=call.transcript,
        sentiment=call.sentiment,
        sentiment_score=call.sentiment_score,
        duration=call.duration,
    )
    call.score = score_result["total_score"]
    call.greeting_quality = score_result["greeting_quality"]
    call.compliance_score = score_result["compliance_score"]
    call.customer_satisfaction = score_result["customer_satisfaction"]
    call.call_clarity = score_result["call_clarity"]
    call.resolution_score = score_result["resolution_score"]
    call.risk_level = score_result["risk_level"]
    call.score_breakdown = json.dumps(score_result)
    call.escalation_required = call.sentiment in ["negative", "angry"]

    duration_minutes = (call.duration or 0) / 60.0
    record_usage(
        db=db,
        tenant_id=call.tenant_id or "public",
        call_id=call.id,
        minutes_used=duration_minutes,
        tokens_used=max(0, len(call.transcript) // 4),
        processing_cost=round(duration_minutes * 0.003, 6),
    )
    db.commit()


async def run_worker(stop_event: asyncio.Event):
    queue = get_queue_service()
    logger.info("Post-call worker started")
    while not stop_event.is_set():
        job = queue.dequeue_analysis(timeout_sec=1)
        if not job:
            await asyncio.sleep(0.2)
            continue

        call_id = job.get("call_id")
        if not call_id:
            continue

        db = SessionLocal()
        try:
            call = db.query(models.Call).filter(models.Call.id == call_id).first()
            if call:
                await analyze_call_by_id(db, call)
                logger.info("Worker analyzed call_id=%s", call_id)
        except Exception as exc:
            logger.exception("Worker failed for call_id=%s error=%s", call_id, exc)
        finally:
            db.close()

    logger.info("Post-call worker stopped")
