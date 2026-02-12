from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    plan = Column(String(50), default="pilot")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(100), ForeignKey("tenants.id"), index=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    full_name = Column(String(200))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Call(Base):
    __tablename__ = "calls"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(100), ForeignKey("tenants.id"), index=True, nullable=False, default="public")
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(200))
    customer_number = Column(String(50), nullable=False)
    customer_name = Column(String(200))

    duration = Column(Integer)
    status = Column(String(50), default="active")
    direction = Column(String(20))
    language = Column(String(20), default="en")
    translated_language = Column(String(20), default="en")

    transcript = Column(Text)
    transcript_segments = Column(Text)
    summary = Column(Text)
    sentiment = Column(String(50))
    sentiment_score = Column(Float)

    score = Column(Integer)
    score_breakdown = Column(Text)
    greeting_quality = Column(Integer)
    compliance_score = Column(Integer)
    customer_satisfaction = Column(Integer)
    call_clarity = Column(Integer)
    resolution_score = Column(Integer)

    risk_level = Column(String(20))
    contains_profanity = Column(Boolean, default=False)
    escalation_required = Column(Boolean, default=False)
    compliance_issues = Column(Text)
    keywords = Column(Text)
    detected_intent = Column(String(200))
    audio_file_path = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("CallMessage", back_populates="call", cascade="all, delete-orphan")


class CallMessage(Base):
    __tablename__ = "call_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=False, index=True)
    speaker = Column(String(20))
    text = Column(Text, nullable=False)
    translated_text = Column(Text)
    timestamp = Column(Float)
    confidence = Column(Float)
    sentiment = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    call = relationship("Call", back_populates="messages")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(100), primary_key=True)
    tenant_id = Column(String(100), ForeignKey("tenants.id"), index=True, nullable=False, default="public")
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True)
    department = Column(String(100))
    total_calls = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    average_sentiment = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(100), ForeignKey("tenants.id"), index=True, nullable=False, default="public")
    name = Column(String(200), nullable=False)
    description = Column(Text)
    rule_type = Column(String(50))
    pattern = Column(String(500))
    required = Column(Boolean, default=False)
    weight = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(100), ForeignKey("tenants.id"), index=True, nullable=False)
    call_id = Column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    minutes_used = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    processing_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class CRMSyncLog(Base):
    __tablename__ = "crm_sync_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(100), ForeignKey("tenants.id"), index=True, nullable=False)
    call_id = Column(String(36), ForeignKey("calls.id"), index=True, nullable=False)
    provider = Column(String(50), nullable=False)
    status = Column(String(30), default="queued")
    synced_at = Column(DateTime, default=datetime.utcnow)
