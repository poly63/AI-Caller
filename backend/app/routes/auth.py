from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app import schemas

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.AuthTokenResponse)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    tenant = db.query(models.Tenant).filter(models.Tenant.id == payload.tenant_id).first()
    if not tenant:
        tenant = models.Tenant(id=payload.tenant_id, name=payload.tenant_name or payload.tenant_id)
        db.add(tenant)
        db.flush()

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = models.User(
        tenant_id=tenant.id,
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, tenant_id=user.tenant_id, role=user.role)
    return {"access_token": token, "token_type": "bearer", "tenant_id": user.tenant_id, "role": user.role}


@router.post("/login", response_model=schemas.AuthTokenResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user.id, tenant_id=user.tenant_id, role=user.role)
    return {"access_token": token, "token_type": "bearer", "tenant_id": user.tenant_id, "role": user.role}
