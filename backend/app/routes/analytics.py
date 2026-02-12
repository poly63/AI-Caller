from collections import Counter
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.deps import get_tenant_id
from app.database import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=schemas.DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    scoped = db.query(models.Call).filter(models.Call.tenant_id == tenant_id)
    total_calls = scoped.with_entities(func.count(models.Call.id)).scalar() or 0
    active_calls = scoped.filter(models.Call.status == "active").with_entities(func.count(models.Call.id)).scalar() or 0
    avg_score = scoped.filter(models.Call.score.isnot(None)).with_entities(func.avg(models.Call.score)).scalar() or 0.0
    avg_sentiment = (
        scoped.filter(models.Call.sentiment_score.isnot(None)).with_entities(func.avg(models.Call.sentiment_score)).scalar() or 0.0
    )
    calls_today = scoped.filter(func.date(models.Call.created_at) == date.today()).with_entities(func.count(models.Call.id)).scalar() or 0

    sentiment_counts = (
        scoped.with_entities(models.Call.sentiment, func.count(models.Call.id))
        .filter(models.Call.sentiment.isnot(None))
        .group_by(models.Call.sentiment)
        .all()
    )
    sentiment_dist = {sent: count for sent, count in sentiment_counts}

    now = datetime.utcnow()
    hourly_data = []
    for i in range(24):
        hour_start = now - timedelta(hours=23 - i)
        hour_end = hour_start + timedelta(hours=1)
        count = (
            scoped.filter(models.Call.created_at >= hour_start, models.Call.created_at < hour_end)
            .with_entities(func.count(models.Call.id))
            .scalar()
            or 0
        )
        hourly_data.append({"hour": hour_start.strftime("%H:00"), "count": count})

    return {
        "total_calls": total_calls,
        "active_calls": active_calls,
        "average_score": round(avg_score, 1),
        "average_sentiment": round(avg_sentiment, 3),
        "calls_today": calls_today,
        "sentiment_distribution": sentiment_dist,
        "hourly_call_volume": hourly_data,
    }


@router.get("/agent/{agent_id}", response_model=schemas.AgentPerformance)
async def get_agent_performance(agent_id: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    calls = db.query(models.Call).filter(models.Call.tenant_id == tenant_id, models.Call.agent_id == agent_id).all()
    if not calls:
        raise HTTPException(status_code=404, detail="Agent not found or has no calls")

    scores = [c.score for c in calls if c.score is not None]
    sentiments = [c.sentiment_score for c in calls if c.sentiment_score is not None]
    durations = [c.duration for c in calls if c.duration is not None]
    all_keywords = []
    for call in calls:
        if call.keywords:
            try:
                import json

                all_keywords.extend(json.loads(call.keywords))
            except Exception:
                pass

    keyword_counts = Counter(all_keywords)
    return {
        "agent_id": agent_id,
        "agent_name": calls[0].agent_name or agent_id,
        "total_calls": len(calls),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "average_sentiment": round(sum(sentiments) / len(sentiments), 3) if sentiments else 0.0,
        "average_duration": round(sum(durations) / len(durations), 1) if durations else 0.0,
        "top_keywords": [kw for kw, _ in keyword_counts.most_common(5)],
    }


@router.get("/agents/leaderboard")
async def get_agents_leaderboard(limit: int = 10, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    rows = (
        db.query(
            models.Call.agent_id,
            models.Call.agent_name,
            func.count(models.Call.id).label("total_calls"),
            func.avg(models.Call.score).label("avg_score"),
            func.avg(models.Call.sentiment_score).label("avg_sentiment"),
        )
        .filter(models.Call.tenant_id == tenant_id, models.Call.score.isnot(None))
        .group_by(models.Call.agent_id, models.Call.agent_name)
        .order_by(func.avg(models.Call.score).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "agent_id": row.agent_id,
            "agent_name": row.agent_name or row.agent_id,
            "total_calls": row.total_calls,
            "average_score": round(row.avg_score, 1) if row.avg_score is not None else 0.0,
            "average_sentiment": round(row.avg_sentiment, 3) if row.avg_sentiment is not None else 0.0,
        }
        for row in rows
    ]


@router.get("/sentiment-trends")
async def get_sentiment_trends(days: int = 7, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    trends = []
    for i in range(days):
        day = date.today() - timedelta(days=days - 1 - i)
        day_calls = (
            db.query(models.Call)
            .filter(models.Call.tenant_id == tenant_id, func.date(models.Call.created_at) == day, models.Call.sentiment.isnot(None))
            .all()
        )
        sentiment_counts = Counter([call.sentiment for call in day_calls])
        trends.append(
            {
                "date": day.isoformat(),
                "total_calls": len(day_calls),
                "positive": sentiment_counts.get("positive", 0),
                "neutral": sentiment_counts.get("neutral", 0),
                "negative": sentiment_counts.get("negative", 0),
                "angry": sentiment_counts.get("angry", 0),
            }
        )
    return trends


@router.get("/risk-alerts")
async def get_risk_alerts(limit: int = 20, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    calls = (
        db.query(models.Call)
        .filter(models.Call.tenant_id == tenant_id, models.Call.risk_level == "high")
        .order_by(models.Call.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "call_id": call.id,
            "agent_id": call.agent_id,
            "agent_name": call.agent_name,
            "customer_number": call.customer_number,
            "sentiment": call.sentiment,
            "score": call.score,
            "created_at": call.created_at.isoformat(),
            "escalation_required": call.escalation_required,
            "summary": call.summary,
        }
        for call in calls
    ]


@router.get("/call-volume")
async def get_call_volume(
    period: str = "daily",
    limit: int = 30,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    data = []
    if period == "daily":
        for i in range(limit):
            day = date.today() - timedelta(days=limit - 1 - i)
            count = (
                db.query(func.count(models.Call.id))
                .filter(models.Call.tenant_id == tenant_id, func.date(models.Call.created_at) == day)
                .scalar()
                or 0
            )
            data.append({"date": day.isoformat(), "count": count})
        return data

    if period == "weekly":
        for i in range(limit):
            week_start = date.today() - timedelta(weeks=limit - 1 - i)
            week_end = week_start + timedelta(days=6)
            count = (
                db.query(func.count(models.Call.id))
                .filter(
                    models.Call.tenant_id == tenant_id,
                    func.date(models.Call.created_at) >= week_start,
                    func.date(models.Call.created_at) <= week_end,
                )
                .scalar()
                or 0
            )
            data.append({"week_start": week_start.isoformat(), "week_end": week_end.isoformat(), "count": count})
        return data

    raise HTTPException(status_code=400, detail="Invalid period. Use 'daily' or 'weekly'")


@router.get("/quality-metrics")
async def get_quality_metrics(db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id)):
    calls = (
        db.query(models.Call)
        .filter(models.Call.tenant_id == tenant_id, models.Call.status == "completed", models.Call.score.isnot(None))
        .all()
    )
    if not calls:
        return {"total_calls": 0, "metrics": {}}

    total = len(calls)
    return {
        "total_calls": total,
        "average_scores": {
            "greeting_quality": round(sum(c.greeting_quality or 0 for c in calls) / total, 1),
            "compliance": round(sum(c.compliance_score or 0 for c in calls) / total, 1),
            "customer_satisfaction": round(sum(c.customer_satisfaction or 0 for c in calls) / total, 1),
            "call_clarity": round(sum(c.call_clarity or 0 for c in calls) / total, 1),
            "resolution": round(sum(c.resolution_score or 0 for c in calls) / total, 1),
        },
        "risk_distribution": {
            "low": sum(1 for c in calls if c.risk_level == "low"),
            "medium": sum(1 for c in calls if c.risk_level == "medium"),
            "high": sum(1 for c in calls if c.risk_level == "high"),
        },
        "calls_requiring_escalation": sum(1 for c in calls if c.escalation_required),
    }
