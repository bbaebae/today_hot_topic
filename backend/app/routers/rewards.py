from __future__ import annotations

import uuid
from datetime import datetime, date, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..config import settings
from ..database import db
from ..schemas.user import RewardRequest, RewardResponse
from ..services.toss_points import issue_points

router = APIRouter()

_REWARD_AMOUNTS: dict[str, int] = {
    "vote": settings.vote_reward_amount,
    "ad": settings.ad_reward_amount,
    "share": settings.share_reward_amount,
}


@router.post("/claim", response_model=RewardResponse)
async def claim_reward(
    body: RewardRequest,
    user: dict = Depends(get_current_user),
):
    client = db()
    today = date.today().isoformat()

    # Check today's earned total
    today_sum_res = (
        client.table("point_transactions")
        .select("amount")
        .eq("user_id", user["id"])
        .eq("status", "success")
        .gte("created_at", f"{today}T00:00:00")
        .execute()
    )
    today_earned = sum(row["amount"] for row in (today_sum_res.data or []))

    amount = _REWARD_AMOUNTS.get(body.reward_type, 0)
    if today_earned + amount > settings.daily_point_limit:
        raise HTTPException(
            status_code=429,
            detail={"error": "DAILY_LIMIT_EXCEEDED", "message": "오늘의 포인트 지급 한도에 도달했습니다."},
        )

    tx_id = str(uuid.uuid4())

    # Persist transaction as pending first
    client.table("point_transactions").insert(
        {
            "id": tx_id,
            "user_id": user["id"],
            "amount": amount,
            "reason": body.reward_type,
            "reference_id": body.reference_id,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()

    # Call Toss mTLS points API
    try:
        await issue_points(
            toss_user_id=user["toss_user_id"],
            amount=amount,
            transaction_id=tx_id,
        )
        final_status = "success"
    except Exception as exc:
        # Mark failed but don't block the response — retry will happen via scheduler
        client.table("point_transactions").update({"status": "failed"}).eq("id", tx_id).execute()
        raise HTTPException(status_code=502, detail=f"포인트 지급 실패: {exc}") from exc

    # Update transaction status and user totals
    client.table("point_transactions").update({"status": final_status}).eq("id", tx_id).execute()
    client.table("users").update(
        {
            "total_points": user["total_points"] + amount,
            "today_earned": today_earned + amount,
        }
    ).eq("id", user["id"]).execute()

    new_balance = user["total_points"] + amount

    return RewardResponse(
        transaction_id=tx_id,
        amount=amount,
        status=final_status,
        current_balance=new_balance,
    )
