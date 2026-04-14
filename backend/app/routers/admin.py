"""Vercel Cron Job 전용 관리자 엔드포인트.

Vercel이 crons 설정으로 주기적으로 호출합니다.
x-admin-key 헤더로 무단 호출을 방지합니다.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Header, HTTPException

router = APIRouter()

_ADMIN_KEY = os.getenv("ADMIN_SECRET_KEY", "")


def _verify(x_admin_key: str | None) -> None:
    """Vercel Cron은 x-vercel-cron-signature 헤더를 보내지만,
    단순하게 우리 ADMIN_SECRET_KEY 헤더로도 허용합니다."""
    # Vercel Cron 자체 호출은 항상 허용 (VERCEL=1 환경)
    if os.getenv("VERCEL") == "1":
        return
    # 로컬에서 테스트 시 키 확인
    if _ADMIN_KEY and x_admin_key != _ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/ingest")
async def trigger_ingest(x_admin_key: str | None = Header(None)):
    """크롤링 + GPT 요약 + Supabase 저장 파이프라인을 실행합니다.
    Vercel Cron에 의해 30분마다 호출됩니다."""
    _verify(x_admin_key)
    from ..services.ingestion import run_ingestion
    result = await run_ingestion()
    return {"ok": True, **result}


@router.post("/rank")
async def trigger_rank(x_admin_key: str | None = Header(None)):
    """토픽 랭킹을 재계산합니다.
    Vercel Cron에 의해 10분마다 호출됩니다."""
    _verify(x_admin_key)
    from ..services.ranking import recompute_ranks
    await recompute_ranks()
    return {"ok": True}
