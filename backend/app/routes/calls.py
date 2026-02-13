import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.core.deps import get_tenant_id
from app.database import get_db
from app.services.queue import get_queue_service
from app.services.transcription import get_transcription_service
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


def _append_transcript_line(call: models.Call, speaker: str, text: str) -> None:
    line = f"{speaker}: {text}".strip()
    call.transcript = f"{(call.transcript or '').strip()}\n{line}".strip()


def _append_transcript_segment(
    call: models.Call,
    *,
    speaker: str,
    original_text: str,
    translated_text: str,
    timestamp: float,
    confidence: float,
) -> None:
    segments = []
    if call.transcript_segments:
        try:
            segments = json.loads(call.transcript_segments)
        except json.JSONDecodeError:
            segments = []
    segments.append(
        {
            "timestamp": timestamp,
            "speaker": speaker,
            "text": original_text,
            "translated_text": translated_text,
            "confidence": confidence,
        }
    )
    call.transcript_segments = json.dumps(segments)


def _store_transcript_message(
    *,
    db: Session,
    call: models.Call,
    speaker: str,
    text: str,
    source_lang: str,
    target_lang: str,
    timestamp: float,
    confidence: float,
) -> dict:
    translated = get_translation_service().translate(
        text,
        source_lang=source_lang,
        target_lang=target_lang,
    )
    translated_text = translated["translated_text"]
    db.add(
        models.CallMessage(
            call_id=call.id,
            speaker=speaker,
            text=text,
            translated_text=translated_text,
            timestamp=timestamp,
            confidence=confidence,
        )
    )
    _append_transcript_line(call, speaker, translated_text)
    _append_transcript_segment(
        call,
        speaker=speaker,
        original_text=text,
        translated_text=translated_text,
        timestamp=timestamp,
        confidence=confidence,
    )
    db.commit()
    return translated


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

    translated = _store_transcript_message(
        db=db,
        call=call,
        speaker=payload.speaker,
        text=payload.text,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
        timestamp=payload.timestamp,
        confidence=1.0,
    )
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

    speaker = "agent"
    source_lang = call.language or "auto"
    target_lang = call.translated_language or "en"
    stream_start = datetime.utcnow()
    try:
        while True:
            data = await websocket.receive()
            if "text" in data:
                try:
                    text_data = json.loads(data["text"] or "{}")
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON payload"})
                    continue
                event_type = text_data.get("type")
                if event_type == "config":
                    speaker = text_data.get("speaker", speaker)
                    source_lang = text_data.get("source_lang", source_lang)
                    target_lang = text_data.get("target_lang", target_lang)
                    await websocket.send_json(
                        {
                            "type": "config_ack",
                            "speaker": speaker,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "call_id": call.id,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                elif event_type == "transcript":
                    text = (text_data.get("text") or "").strip()
                    if not text:
                        continue
                    speaker = text_data.get("speaker", speaker)
                    source_lang = text_data.get("source_lang", source_lang)
                    target_lang = text_data.get("target_lang", target_lang)
                    ts = float(text_data.get("timestamp") or (datetime.utcnow() - stream_start).total_seconds())
                    translated = _store_transcript_message(
                        db=db,
                        call=call,
                        speaker=speaker,
                        text=text,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        timestamp=ts,
                        confidence=1.0,
                    )
                    await websocket.send_json(
                        {
                            "type": "transcript",
                            "speaker": speaker,
                            "text": text,
                            "translated_text": translated["translated_text"],
                            "timestamp": ts,
                            "confidence": 1.0,
                        }
                    )
                elif event_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            elif "bytes" in data:
                audio_bytes = data["bytes"] or b""
                if len(audio_bytes) < 2:
                    continue
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                segments = await asyncio.to_thread(get_transcription_service().transcribe_audio, audio_array)
                for segment in segments:
                    text = (segment.get("text") or "").strip()
                    if not text:
                        continue
                    ts = float(segment.get("start", (datetime.utcnow() - stream_start).total_seconds()))
                    conf = float(segment.get("confidence", 1.0))
                    translated = _store_transcript_message(
                        db=db,
                        call=call,
                        speaker=speaker,
                        text=text,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        timestamp=ts,
                        confidence=conf,
                    )
                    await websocket.send_json(
                        {
                            "type": "transcript",
                            "speaker": speaker,
                            "text": text,
                            "translated_text": translated["translated_text"],
                            "timestamp": ts,
                            "confidence": conf,
                        }
                    )
                if not segments:
                    await websocket.send_json({"type": "processing", "timestamp": datetime.utcnow().isoformat()})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for call=%s tenant=%s", call.id, tenant_id)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        await websocket.close()
