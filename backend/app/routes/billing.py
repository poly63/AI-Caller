from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_tenant_id, require_roles
from app.services.billing import summarize_usage

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/usage")
def get_usage_summary(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _=Depends(require_roles("admin", "manager", "viewer")),
):
    return summarize_usage(db, tenant_id)
