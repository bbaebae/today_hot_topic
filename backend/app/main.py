from __future__ import annotations

import base64
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth, topics, polls, rewards, users, admin
from .scheduler import start_scheduler, stop_scheduler


def _restore_certs() -> None:
    """base64 환경변수에서 mTLS 인증서 파일을 복원합니다."""
    cert_map = {
        "TOSS_MTLS_CERT_B64": settings.toss_mtls_cert_path,
        "TOSS_MTLS_KEY_B64":  settings.toss_mtls_key_path,
        "TOSS_MTLS_CA_B64":   settings.toss_mtls_ca_path,
    }
    for env_key, file_path in cert_map.items():
        b64 = os.getenv(env_key)
        if not b64:
            continue
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(b64))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _restore_certs()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="오늘 왜 떠? API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix="/api/v1/auth",    tags=["auth"])
app.include_router(topics.router,  prefix="/api/v1/topics",  tags=["topics"])
app.include_router(polls.router,   prefix="/api/v1/polls",   tags=["polls"])
app.include_router(rewards.router, prefix="/api/v1/rewards", tags=["rewards"])
app.include_router(users.router,   prefix="/api/v1/users",   tags=["users"])
app.include_router(admin.router,   prefix="/api/v1/admin",   tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}
