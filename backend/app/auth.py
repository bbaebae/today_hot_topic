"""Toss OAuth2 기반 인증.

흐름:
  1. 프론트엔드: appLogin() SDK 호출 → authorizationCode 수신
  2. 프론트엔드: POST /api/v1/auth/token { authorizationCode } 호출
  3. 백엔드: Toss API로 authorizationCode → accessToken + userKey 교환 (mTLS)
  4. 백엔드: userKey로 로컬 user 행 생성/조회 → 서버 세션 JWT 발급
  5. 이후 모든 API 요청: Authorization: Bearer {서버JWT}
"""
from __future__ import annotations

import ssl
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .database import db

bearer = HTTPBearer(auto_error=False)

_TOSS_TOKEN_URL = f"{settings.toss_api_base_url}/api-partner/v1/apps-in-toss/user/oauth2/generate-token"
_TOSS_ME_URL = f"{settings.toss_api_base_url}/api-partner/v1/apps-in-toss/user/oauth2/login-me"


def _build_mtls_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=settings.toss_mtls_ca_path)
    ctx.load_cert_chain(
        certfile=settings.toss_mtls_cert_path,
        keyfile=settings.toss_mtls_key_path,
    )
    return ctx


async def exchange_authorization_code(authorization_code: str, referrer: str) -> dict:
    """
    Toss authorizationCode → accessToken + userKey 교환 (mTLS).
    Returns: { accessToken, refreshToken, userKey }
    """
    ssl_ctx = _build_mtls_context()
    async with httpx.AsyncClient(verify=ssl_ctx, timeout=10.0) as client:
        # Step 1: 토큰 발급
        token_resp = await client.post(
            _TOSS_TOKEN_URL,
            json={"authorizationCode": authorization_code, "referrer": referrer},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        if token_data.get("resultType") != "SUCCESS":
            raise HTTPException(status_code=401, detail=token_data.get("error", {}).get("reason", "Token exchange failed"))

        access_token = token_data["success"]["accessToken"]
        refresh_token = token_data["success"]["refreshToken"]

        # Step 2: userKey 조회
        me_resp = await client.get(
            _TOSS_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        me_resp.raise_for_status()
        me_data = me_resp.json()

        if me_data.get("resultType") != "SUCCESS":
            raise HTTPException(status_code=401, detail="Failed to fetch user info")

        user_key: str = me_data["success"]["userKey"]

    return {
        "toss_access_token": access_token,
        "toss_refresh_token": refresh_token,
        "user_key": user_key,
    }


def issue_server_jwt(user_id: str) -> str:
    """로컬 user.id 기반 서버 세션 JWT를 발급합니다."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_server_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_or_create_user(user_key: str) -> dict:
    """userKey로 로컬 user 행을 조회하거나 신규 생성합니다."""
    client = db()
    res = (
        client.table("users")
        .select("*")
        .eq("toss_user_id", user_key)
        .maybe_single()
        .execute()
    )
    if res.data:
        return res.data

    new_user = {
        "id": str(uuid.uuid4()),
        "toss_user_id": user_key,
        "is_premium": False,
        "total_points": 0,
        "today_earned": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client.table("users").insert(new_user).execute()
    return new_user


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = _decode_server_jwt(creds.credentials)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    res = db().table("users").select("*").eq("id", user_id).maybe_single().execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="User not found")
    return res.data
