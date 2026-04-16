"""APScheduler 기반 크롤링 + 랭킹 갱신 잡.

크롤링 전략:
  - 커뮤니티/뉴스 통합 인제스션: 하루 4회 (KST 기준)
      02:00 — 심야(22~01시) 업로드 글 반응 쌓인 후
      10:00 — 아침(07~09시) 출근길 + 전날 누적
      15:00 — 점심(12~13시) 이후 반응 쌓인 글
      21:00 — 저녁(18~20시) 퇴근 후 글
  - 랭킹 재계산: 30분마다 (가볍고 빠름)
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None

_KST = "Asia/Seoul"


async def _cleanup_old_topics() -> None:
    """24시간 이상 된 토픽·투표를 삭제합니다."""
    from datetime import datetime, timezone, timedelta
    from .database import db
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        client = db()
        old = client.table("topics").select("id").lt("created_at", cutoff).execute()
        old_ids = [r["id"] for r in (old.data or [])]
        if old_ids:
            client.table("polls").delete().in_("topic_id", old_ids).execute()
            client.table("topics").delete().in_("id", old_ids).execute()
            logger.info("Cleaned up %d old topics", len(old_ids))
    except Exception:
        logger.exception("Cleanup job failed")


async def _run_ingestion() -> None:
    await _cleanup_old_topics()
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
    _scheduler = AsyncIOScheduler(timezone=_KST)

    # 인제스션: 하루 4회 (KST)
    for hour in (2, 10, 15, 21):
        _scheduler.add_job(
            _run_ingestion,
            trigger=CronTrigger(hour=hour, minute=0, timezone=_KST),
            id=f"ingestion_{hour:02d}",
            replace_existing=True,
            max_instances=1,
        )

    # 랭킹: 30분마다
    _scheduler.add_job(
        _run_ranking,
        trigger=IntervalTrigger(minutes=30),
        id="ranking",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info("Scheduler started: ingestion at 02/10/15/21 KST, ranking every 30min")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
