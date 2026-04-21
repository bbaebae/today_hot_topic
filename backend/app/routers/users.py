from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import db
from ..schemas.user import UserProfileResponse, UserSchema

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    user_schema = UserSchema(
        id=user["id"],
        toss_user_id=user["toss_user_id"],
        is_premium=user.get("is_premium", False),
        created_at=user["created_at"],
    )

    return UserProfileResponse(user=user_schema)


class ActivatePremiumRequest(BaseModel):
    order_id: str
    sku: str


@router.post("/me/premium", response_model=UserProfileResponse)
async def activate_premium(
    body: ActivatePremiumRequest,
    user: dict = Depends(get_current_user),
):
    """인앱 결제 완료 후 프리미엄 상태를 활성화합니다."""
    client = db()

    # 중복 처리 방지: order_id가 이미 처리된 건인지 확인
    existing = (
        client.table("iap_orders")
        .select("id")
        .eq("order_id", body.order_id)
        .maybe_single()
        .execute()
    )
    if existing.data:
        # 이미 처리된 주문 — 현재 유저 상태만 반환
        user_schema = UserSchema(
            id=user["id"],
            toss_user_id=user["toss_user_id"],
            is_premium=user.get("is_premium", True),
            created_at=user["created_at"],
        )
        return UserProfileResponse(user=user_schema)

    # 주문 기록 저장
    from datetime import datetime, timezone
    import uuid
    client.table("iap_orders").insert({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "order_id": body.order_id,
        "sku": body.sku,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    # 유저 프리미엄 활성화
    client.table("users").update({"is_premium": True}).eq("id", user["id"]).execute()

    user_schema = UserSchema(
        id=user["id"],
        toss_user_id=user["toss_user_id"],
        is_premium=True,
        created_at=user["created_at"],
    )
    return UserProfileResponse(user=user_schema)
