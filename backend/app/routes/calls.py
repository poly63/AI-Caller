import json
import logging
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.core.deps import get_tenant_id
from app.database import get_db
from app.services.queue import get_queue_service
from app.services.translation import get_translation_service
from app.workers.post_call_worker import analyze_call_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calls", tags=["calls"])


def _get_call_for_tenant(db: Session, tenant_id: str, call_id: str) -> models.Call | None:
    return (
        db.query(models.Call)
        .filter(models.Call.id == call_id, models.Call.tenant_id == tenant_id)
        .first()
    )


@router.post("/start", response_model=schemas.CallResponse)
async def start_call(
    call_data: schemas.CallCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    call = models.Call(
        tenant_id=tenant_id,
        agent_id=call_data.agent_id,
        agent_name=call_data.agent_name,
        customer_number=call_data.customer_number,
        customer_name=call_data.customer_name,
        direction=call_data.direction,
        status="active",
        language=call_data.language,
        translated_language=call_data.translated_language,
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    logger.info("Started call id=%s tenant=%s", call.id, tenant_id)
    return call


@router.get("/{call_id}", response_model=schemas.CallDetailResponse)
async def get_call(call_id: UUID, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.get("/", response_model=List[schemas.CallResponse])
async def list_calls(
    skip: int = 0,
    limit: int = 50,
    agent_id: str | None = None,
    status: str | None = None,
    sentiment: str | None = None,
    min_score: int | None = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    query = db.query(models.Call).filter(models.Call.tenant_id == tenant_id)
    if agent_id:
        query = query.filter(models.Call.agent_id == agent_id)
    if status:
        query = query.filter(models.Call.status == status)
    if sentiment:
        query = query.filter(models.Call.sentiment == sentiment)
    if min_score is not None:
        query = query.filter(models.Call.score >= min_score)
    return query.order_by(models.Call.created_at.desc()).offset(skip).limit(limit).all()


@router.patch("/{call_id}", response_model=schemas.CallResponse)
async def update_call(
    call_id: UUID,
    call_update: schemas.CallUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    for field, value in call_update.model_dump(exclude_unset=True).items():
        setattr(call, field, value)
    db.commit()
    db.refresh(call)
    return call


@router.post("/{call_id}/transcript")
async def add_transcript_chunk(
    call_id: UUID,
    payload: schemas.TranscriptChunk,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    translated = get_translation_service().translate(
        payload.text,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
    )
    message = models.CallMessage(
        call_id=call.id,
        speaker=payload.speaker,
        text=payload.text,
        translated_text=translated["translated_text"],
        timestamp=payload.timestamp,
        confidence=1.0,
    )
    db.add(message)
    current = call.transcript or ""
    line = f"{payload.speaker}: {translated['translated_text']}"
    call.transcript = f"{current}\n{line}".strip()
    db.commit()
    return {"status": "ok", "translated_text": translated["translated_text"]}


@router.post("/{call_id}/end")
async def end_call(call_id: UUID, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call.status = "completed"
    call.ended_at = datetime.utcnow()
    if call.started_at:
        call.duration = int((call.ended_at - call.started_at).total_seconds())
    db.commit()

    queue_payload = {"call_id": call.id, "tenant_id": tenant_id}
    queued = get_queue_service().enqueue_analysis(queue_payload)
    if not queued:
        await analyze_call_by_id(db, call)

    return {"status": "ended", "call_id": str(call_id), "duration": call.duration, "queued": queued}


@router.post("/{call_id}/analyze")
async def analyze_call(call_id: UUID, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    if not call.transcript:
        raise HTTPException(status_code=400, detail="No transcript available")

    await analyze_call_by_id(db, call)
    db.refresh(call)
    return {
        "status": "analyzed",
        "call_id": str(call_id),
        "score": call.score,
        "sentiment": call.sentiment,
        "risk_level": call.risk_level,
        "summary": call.summary,
    }


@router.post("/{call_id}/messages", response_model=schemas.CallResponse)
async def add_message(
    call_id: UUID,
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    db.add(
        models.CallMessage(
            call_id=call.id,
            speaker=message.speaker,
            text=message.text,
            translated_text=message.text,
            timestamp=message.timestamp,
            confidence=message.confidence,
        )
    )
    call.transcript = f"{(call.transcript or '').strip()}\n{message.speaker}: {message.text}".strip()
    db.commit()
    db.refresh(call)
    return call


@router.delete("/{call_id}")
async def delete_call(call_id: UUID, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    db.delete(call)
    db.commit()
    return {"status": "deleted", "call_id": str(call_id)}


@router.websocket("/ws/{call_id}")
async def websocket_call_stream(
    websocket: WebSocket,
    call_id: UUID,
    db: Session = Depends(get_db),
):
    tenant_id = websocket.headers.get("x-tenant-id", "public")
    await websocket.accept()
    call = _get_call_for_tenant(db, tenant_id, str(call_id))
    if not call:
        await websocket.send_json({"error": "Call not found"})
        await websocket.close()
        return

    transcript_parts = []
    try:
        while True:
            data = await websocket.receive()
            if "text" in data:
                text_data = json.loads(data["text"])
                if text_data.get("type") == "transcript":
                    transcript_parts.append(text_data.get("text", ""))
                    await websocket.send_json(
                        {
                            "status": "received",
                            "text": text_data.get("text"),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
            elif "bytes" in data:
                await websocket.send_json({"status": "processing", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        if transcript_parts:
            call.transcript = " ".join(transcript_parts)
            db.commit()
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        await websocket.close()
