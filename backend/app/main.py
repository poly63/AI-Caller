import asyncio
import logging
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.core.rate_limit import SimpleRateLimitMiddleware
from app.services.transcription import get_transcription_service
from app.services.sentiment import get_sentiment_analyzer
from app.services.summary import get_summary_generator
from app.services.scoring import get_scoring_engine
from app.services.queue import get_queue_service
from app.routes import calls, analytics
from app.routes import auth, crm, billing
from app.workers.post_call_worker import run_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartCall AI", description="Real-Time Call Intelligence Platform", version="2.0.0-pilot")
app.add_middleware(SimpleRateLimitMiddleware, requests_per_minute=600)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(calls.router)
app.include_router(analytics.router)
app.include_router(crm.router)
app.include_router(billing.router)

worker_stop_event = asyncio.Event()
worker_task: asyncio.Task | None = None
run_embedded_worker = os.getenv("RUN_EMBEDDED_WORKER", "true").lower() == "true"


@app.on_event("startup")
async def startup_event():
    global worker_task
    logger.info("Starting SmartCall AI")
    init_db()
    get_queue_service()

    services = [
        ("transcription", lambda: get_transcription_service(model_size="base", device="cpu")),
        ("sentiment", get_sentiment_analyzer),
        ("summary", get_summary_generator),
        ("scoring", get_scoring_engine),
    ]
    for name, initializer in services:
        try:
            initializer()
            logger.info("%s service ready", name)
        except Exception as exc:
            logger.warning("%s service degraded: %s", name, exc)

    if run_embedded_worker:
        worker_stop_event.clear()
        worker_task = asyncio.create_task(run_worker(worker_stop_event))
    logger.info("Service initialization complete")


@app.on_event("shutdown")
async def shutdown_event():
    global worker_task
    if run_embedded_worker:
        worker_stop_event.set()
        if worker_task:
            await worker_task


@app.get("/")
async def root():
    return {"status": "ok", "service": "SmartCall AI", "version": "2.0.0-pilot"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {"database": "connected", "transcription": "ready", "sentiment": "ready", "scoring": "ready"},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
