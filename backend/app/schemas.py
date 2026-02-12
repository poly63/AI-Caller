from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    tenant_id: str = "public"
    tenant_name: Optional[str] = None
    email: str
    full_name: Optional[str] = None
    password: str = Field(min_length=8)
    role: str = "admin"


class UserLogin(BaseModel):
    email: str
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    tenant_id: str
    role: str


class CallCreate(BaseModel):
    agent_id: str
    agent_name: Optional[str] = None
    customer_number: str
    customer_name: Optional[str] = None
    direction: str = "inbound"
    language: str = "en"
    translated_language: str = "en"


class CallUpdate(BaseModel):
    status: Optional[str] = None
    duration: Optional[int] = None
    transcript: Optional[str] = None
    ended_at: Optional[datetime] = None


class MessageCreate(BaseModel):
    speaker: str
    text: str
    timestamp: float
    confidence: Optional[float] = 1.0


class TranscriptChunk(BaseModel):
    speaker: str = "agent"
    text: str
    timestamp: float = 0
    source_lang: str = "auto"
    target_lang: str = "en"


class CallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: Optional[str] = "public"
    agent_id: str
    agent_name: Optional[str]
    customer_number: str
    customer_name: Optional[str]
    duration: Optional[int]
    status: str
    direction: str
    language: Optional[str]
    translated_language: Optional[str]

    transcript: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    score: Optional[int]
    risk_level: Optional[str]

    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]


class CallDetailResponse(CallResponse):
    model_config = ConfigDict(from_attributes=True)

    score_breakdown: Optional[str]
    greeting_quality: Optional[int]
    compliance_score: Optional[int]
    customer_satisfaction: Optional[int]
    call_clarity: Optional[int]
    resolution_score: Optional[int]
    contains_profanity: bool
    escalation_required: bool
    compliance_issues: Optional[str]
    keywords: Optional[str]
    detected_intent: Optional[str]
    audio_file_path: Optional[str]


class SentimentAnalysisResult(BaseModel):
    sentiment: str
    score: float
    confidence: float


class CallSummaryResult(BaseModel):
    summary: str
    key_points: List[str]
    customer_intent: str
    action_items: List[str]


class CallScoreResult(BaseModel):
    total_score: int
    greeting_quality: int
    compliance_score: int
    customer_satisfaction: int
    call_clarity: int
    resolution_score: int
    risk_level: str
    recommendations: List[str]


class DashboardStats(BaseModel):
    total_calls: int
    active_calls: int
    average_score: float
    average_sentiment: float
    calls_today: int
    sentiment_distribution: dict
    hourly_call_volume: List[dict]


class AgentPerformance(BaseModel):
    agent_id: str
    agent_name: str
    total_calls: int
    average_score: float
    average_sentiment: float
    average_duration: float
    top_keywords: List[str]


class CRMSyncRequest(BaseModel):
    call_id: str
    provider: str = "zoho"
    payload: dict = Field(default_factory=dict)


class CRMSyncResponse(BaseModel):
    status: str
    provider: str
    call_id: str
