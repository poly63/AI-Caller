from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_tenant_id, require_roles
from app.services.crm import get_crm_service
from app import models
from app import schemas

router = APIRouter(prefix="/api/crm", tags=["crm"])


@router.post("/sync", response_model=schemas.CRMSyncResponse)
def sync_call(payload: schemas.CRMSyncRequest, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id), _=Depends(require_roles("admin", "manager"))):
    service = get_crm_service()
    result = service.sync_call(payload.provider, payload.model_dump())
    log = models.CRMSyncLog(
        tenant_id=tenant_id,
        call_id=payload.call_id,
        provider=payload.provider,
        status=result["status"],
        synced_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return {"status": result["status"], "provider": payload.provider, "call_id": payload.call_id}


@router.get("/logs")
def get_sync_logs(db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id), _=Depends(require_roles("admin", "manager", "viewer"))):
    logs = (
        db.query(models.CRMSyncLog)
        .filter(models.CRMSyncLog.tenant_id == tenant_id)
        .order_by(models.CRMSyncLog.synced_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "call_id": row.call_id,
            "provider": row.provider,
            "status": row.status,
            "synced_at": row.synced_at.isoformat() if row.synced_at else None,
        }
        for row in logs
    ]
