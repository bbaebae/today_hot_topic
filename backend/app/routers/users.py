from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user
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
