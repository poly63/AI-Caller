import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from app.core.config import settings

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", settings.database_url)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _ensure_sqlite_columns():
    if not DATABASE_URL.startswith("sqlite"):
        return

    alter_statements = [
        "ALTER TABLE calls ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'public'",
        "ALTER TABLE calls ADD COLUMN language VARCHAR(20) DEFAULT 'en'",
        "ALTER TABLE calls ADD COLUMN translated_language VARCHAR(20) DEFAULT 'en'",
        "ALTER TABLE calls ADD COLUMN audio_file_path TEXT",
        "ALTER TABLE calls ADD COLUMN updated_at DATETIME",
        "ALTER TABLE call_messages ADD COLUMN translated_text TEXT",
        "ALTER TABLE agents ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'public'",
        "ALTER TABLE compliance_rules ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'public'",
    ]
    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                # Existing column or older table missing; keep startup resilient.
                pass


def _seed_default_tenant():
    from app import models

    with SessionLocal() as db:
        tenant = db.query(models.Tenant).filter(models.Tenant.id == settings.default_tenant_id).first()
        if not tenant:
            db.add(models.Tenant(id=settings.default_tenant_id, name="Default Tenant", plan="pilot"))
            db.commit()


def init_db():
    from app.models import Base

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
    _seed_default_tenant()
    print("Database tables created successfully")


if __name__ == "__main__":
    init_db()
