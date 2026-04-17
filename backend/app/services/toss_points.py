"""Toss 포인트 지급 API — mTLS 2단계 실행.

Step 1: GET  /api-partner/v1/apps-in-toss/promotion/execute-promotion/get-key
Step 2: POST /api-partner/v1/apps-in-toss/promotion/execute-promotion
Step 3: POST /api-partner/v1/apps-in-toss/promotion/execution-result (상태 확인)
"""
from __future__ import annotations

import asyncio
import ssl

import httpx

from ..config import settings

_BASE = settings.toss_api_base_url
_GET_KEY_URL = f"{_BASE}/api-partner/v1/apps-in-toss/promotion/execute-promotion/get-key"
_EXECUTE_URL = f"{_BASE}/api-partner/v1/apps-in-toss/promotion/execute-promotion"
_RESULT_URL = f"{_BASE}/api-partner/v1/apps-in-toss/promotion/execution-result"


def _build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.load_cert_chain(
        certfile=settings.toss_mtls_cert_path,
        keyfile=settings.toss_mtls_key_path,
    )
    return ctx


async def issue_points(
    toss_user_key: str,
    amount: int,
    transaction_id: str,
) -> dict:
    """
    Toss 포인트 지급 2단계 실행.

    Args:
        toss_user_key: Toss userKey (login-me API에서 받은 값)
        amount: 지급할 포인트 (원 단위)
        transaction_id: 우리 DB의 point_transaction.id (멱등성 키)

    Returns:
        Toss 실행 결과 dict

    Raises:
        httpx.HTTPStatusError: Toss API 오류
    """
    ssl_ctx = _build_ssl_context()
    headers = {"x-toss-user-key": toss_user_key}

    async with httpx.AsyncClient(verify=ssl_ctx, timeout=10.0) as client:
        # Step 1: 프로모션 키 발급
        key_resp = await client.post(
            _GET_KEY_URL,
            headers=headers,
            json={},
        )
        key_resp.raise_for_status()
        key_data = key_resp.json()

        if key_data.get("resultType") != "SUCCESS":
            error = key_data.get("error", {})
            raise RuntimeError(f"[{error.get('errorCode')}] {error.get('reason')}")

        promo_key = key_data["success"]["key"]

        # Step 2: 포인트 지급 실행
        exec_resp = await client.post(
            _EXECUTE_URL,
            headers=headers,
            json={
                "promotionCode": settings.toss_promotion_code,
                "key": promo_key,
                "amount": amount,
            },
        )
        exec_resp.raise_for_status()
        exec_data = exec_resp.json()

        if exec_data.get("resultType") != "SUCCESS":
            error = exec_data.get("error", {})
            error_code = error.get("errorCode", "")
            # 4110: 내부 오류 → 재시도
            if error_code == "4110":
                await asyncio.sleep(1)
                return await issue_points(toss_user_key, amount, transaction_id)
            raise RuntimeError(f"[{error_code}] {error.get('reason')}")

        return exec_data["success"]


async def check_result(toss_user_key: str, promo_key: str) -> str:
    """포인트 지급 상태 확인. Returns: 'PENDING' | 'SUCCESS' | 'FAILED'"""
    ssl_ctx = _build_ssl_context()
    async with httpx.AsyncClient(verify=ssl_ctx, timeout=10.0) as client:
        resp = await client.post(
            _RESULT_URL,
            headers={"x-toss-user-key": toss_user_key},
            json={
                "promotionCode": settings.toss_promotion_code,
                "key": promo_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("resultType") == "SUCCESS":
            return data["success"]
        return "FAILED"
