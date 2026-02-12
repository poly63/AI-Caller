import json
import logging
from typing import Optional
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)
CALL_ANALYSIS_QUEUE = "smartcall:analysis_queue"


class QueueService:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        try:
            self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            self.client.ping()
        except Exception as exc:
            self.client = None
            logger.warning("Redis unavailable, queue disabled: %s", exc)

    def enqueue_analysis(self, payload: dict) -> bool:
        if not self.client:
            return False
        self.client.rpush(CALL_ANALYSIS_QUEUE, json.dumps(payload))
        return True

    def dequeue_analysis(self, timeout_sec: int = 2) -> Optional[dict]:
        if not self.client:
            return None
        result = self.client.blpop(CALL_ANALYSIS_QUEUE, timeout=timeout_sec)
        if not result:
            return None
        _, raw = result
        return json.loads(raw)


_queue_service = None


def get_queue_service() -> QueueService:
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service
