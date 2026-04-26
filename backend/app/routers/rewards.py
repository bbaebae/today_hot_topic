"""포인트 지급 라우터 — 리워드 광고 시청 후 포인트 적립, 토스 포인트 변환."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..database import db
from ..services.toss_points import issue_points
from ..config import settings

router = APIRouter()

AD_REWARD_POINTS = 10


@router.post("/ad-watched")
async def record_ad_watch(user: dict = Depends(get_current_user)):
    """리워드 광고 시청 완료 후 포인트를 적립합니다."""
    client = db()
    current = user.get("total_points", 0)
    new_total = current + AD_REWARD_POINTS
    client.table("users").update({"total_points": new_total}).eq("id", user["id"]).execute()
    return {"total_points": new_total, "earned": AD_REWARD_POINTS}


class ConvertRequest(BaseModel):
    amount: int


@router.post("/convert")
async def convert_to_toss_points(
    body: ConvertRequest,
    user: dict = Depends(get_current_user),
):
    """앱 포인트를 토스 포인트로 변환합니다."""
    if not settings.toss_promotion_code:
        raise HTTPException(status_code=503, detail="포인트 변환 서비스가 준비 중이에요.")

    amount = body.amount
    current = user.get("total_points", 0)

    if amount <= 0:
        raise HTTPException(status_code=400, detail="변환할 포인트를 확인해 주세요.")
    if amount > current:
        raise HTTPException(status_code=400, detail="포인트가 부족합니다.")

    client = db()
    new_total = current - amount
    # 포인트 선차감 (중복 변환 방지)
    client.table("users").update({"total_points": new_total}).eq("id", user["id"]).execute()

    try:
        toss_user_key = user["toss_user_id"]
        await issue_points(toss_user_key, amount, user["id"])
        return {"total_points": new_total, "converted": amount}
    except Exception as exc:
        # Toss API 실패 시 롤백
        client.table("users").update({"total_points": current}).eq("id", user["id"]).execute()
        raise HTTPException(status_code=502, detail="포인트 변환에 실패했어요. 잠시 후 다시 시도해 주세요.") from exc
