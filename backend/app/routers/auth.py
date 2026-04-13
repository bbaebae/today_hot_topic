"""Toss OAuth2 토큰 교환 라우터."""
from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from ..auth import exchange_authorization_code, get_or_create_user, issue_server_jwt

router = APIRouter()


class TokenRequest(BaseModel):
    authorization_code: str
    referrer: str = "DEFAULT"  # "SANDBOX" | "DEFAULT"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


@router.post("/token", response_model=TokenResponse)
async def get_token(body: TokenRequest):
    """
    프론트엔드 appLogin() 결과로 받은 authorizationCode를 서버 JWT로 교환합니다.
    """
    try:
        toss_data = await exchange_authorization_code(
            body.authorization_code, body.referrer
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Toss API error: {exc}") from exc

    user = get_or_create_user(toss_data["user_key"])
    server_jwt = issue_server_jwt(user["id"])

    return TokenResponse(access_token=server_jwt)
