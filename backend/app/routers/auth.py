"""Toss OAuth2 토큰 교환 라우터."""
from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request

from ..auth import exchange_authorization_code, get_or_create_user, issue_server_jwt
from ..database import db

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


@router.post("/disconnect")
async def disconnect(request: Request):
    """토스 앱에서 연결 끊기 시 호출되는 콜백. 사용자 데이터를 삭제합니다."""
    try:
        body = await request.json()
        toss_user_key = body.get("userKey") or body.get("user_key", "")
        if toss_user_key:
            client = db()
            client.table("users").delete().eq("toss_user_id", toss_user_key).execute()
    except Exception:
        pass  # 콜백 실패해도 토스에 200 반환 필요
    return {"ok": True}
