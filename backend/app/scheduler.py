"""APScheduler 기반 주기적 크롤링 + 랭킹 갱신 잡."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import settings

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def _run_ingestion() -> None:
    from .services.ingestion import run_ingestion
    try:
        result = await run_ingestion()
        logger.info("Ingestion complete: %s", result)
    except Exception:
        logger.exception("Ingestion job failed")


async def _run_ranking() -> None:
    from .services.ranking import recompute_ranks
    try:
        await recompute_ranks()
        logger.info("Ranking recomputed")
    except Exception:
        logger.exception("Ranking job failed")


def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        _run_ingestion,
        trigger=IntervalTrigger(minutes=settings.crawler_interval_minutes),
        id="ingestion",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.add_job(
        _run_ranking,
        trigger=IntervalTrigger(minutes=10),
        id="ranking",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started (ingestion every %dmin, ranking every 10min)",
        settings.crawler_interval_minutes,
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
