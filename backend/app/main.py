from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth, topics, polls, rewards, users, admin
from .scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
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
