from typing import Dict
from sqlalchemy.orm import Session

from app import models


def record_usage(
    db: Session,
    tenant_id: str,
    call_id: str,
    minutes_used: float,
    tokens_used: int = 0,
    processing_cost: float = 0.0,
) -> models.UsageLog:
    usage = models.UsageLog(
        tenant_id=tenant_id,
        call_id=call_id,
        minutes_used=minutes_used,
        tokens_used=tokens_used,
        processing_cost=processing_cost,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def summarize_usage(db: Session, tenant_id: str) -> Dict:
    rows = db.query(models.UsageLog).filter(models.UsageLog.tenant_id == tenant_id).all()
    return {
        "total_calls": len({r.call_id for r in rows}),
        "total_minutes": round(sum(r.minutes_used or 0 for r in rows), 2),
        "total_tokens": int(sum(r.tokens_used or 0 for r in rows)),
        "estimated_cost": round(sum(r.processing_cost or 0 for r in rows), 4),
    }
