from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..database import db
from ..schemas.user import PointTransactionSchema, UserProfileResponse, UserSchema

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    client = db()

    tx_res = (
        client.table("point_transactions")
        .select("id, amount, reason, status, created_at")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    user_schema = UserSchema(
        id=user["id"],
        toss_user_id=user["toss_user_id"],
        is_premium=user.get("is_premium", False),
        total_points=user.get("total_points", 0),
        today_earned=user.get("today_earned", 0),
        created_at=user["created_at"],
    )

    transactions = [
        PointTransactionSchema(
            id=row["id"],
            amount=row["amount"],
            reason=row["reason"],
            status=row["status"],
            created_at=row["created_at"],
        )
        for row in (tx_res.data or [])
    ]

    return UserProfileResponse(user=user_schema, transactions=transactions)
