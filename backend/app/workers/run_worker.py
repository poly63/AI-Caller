import asyncio
import logging

from app.database import init_db
from app.workers.post_call_worker import run_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    init_db()
    stop_event = asyncio.Event()
    logger.info("Starting standalone post-call worker")
    await run_worker(stop_event)


if __name__ == "__main__":
    asyncio.run(main())
