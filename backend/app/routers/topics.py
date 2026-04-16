from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..database import db
from ..schemas.topic import TopicDetail, TopicListItem, TopicsResponse

router = APIRouter()

Category = Literal["story", "society", "economy", "sports", "love"]


@router.get("", response_model=TopicsResponse)
async def list_topics(
    category: Category | None = Query(None, description="썰/사회/경제/스포츠/연애 필터"),
):
    client = db()

    if category:
        res = (
            client.table("topics")
            .select("id, title, category, image_url, view_count, rank, created_at")
            .eq("category", category)
            .order("rank")
            .limit(50)
            .execute()
        )
        topics = res.data or []

        # 해당 카테고리 토픽이 없으면 전체 최신 토픽으로 폴백
        if not topics:
            res = (
                client.table("topics")
                .select("id, title, category, image_url, view_count, rank, created_at")
                .order("created_at", desc=True)
                .limit(30)
                .execute()
            )
            topics = res.data or []
    else:
        res = (
            client.table("topics")
            .select("id, title, category, image_url, view_count, rank, created_at")
            .order("view_count", desc=True)
            .limit(50)
            .execute()
        )
        topics = res.data or []

    return TopicsResponse(topics=[TopicListItem(**row) for row in topics])


@router.get("/{topic_id}", response_model=TopicDetail)
async def get_topic(topic_id: str):
    client = db()

    topic_res = (
        client.table("topics")
        .select("*")
        .eq("id", topic_id)
        .maybe_single()
        .execute()
    )
    if not topic_res.data:
        raise HTTPException(status_code=404, detail="Topic not found")

    row = topic_res.data
    # summary_json은 JSON 배열 문자열 또는 일반 문자열일 수 있음
    raw_summary = row.get("summary_json") or "[]"
    try:
        parsed = json.loads(raw_summary) if isinstance(raw_summary, str) else raw_summary
        summary: list[str] = parsed if isinstance(parsed, list) else [str(parsed)]
    except (json.JSONDecodeError, TypeError):
        summary = [raw_summary] if raw_summary else []

    poll_res = (
        client.table("polls")
        .select("*")
        .eq("topic_id", topic_id)
        .maybe_single()
        .execute()
    )
    poll_data = poll_res.data or {}

    # Increment view count (fire-and-forget, ignore errors)
    try:
        client.rpc("increment_view_count", {"topic_id": topic_id}).execute()
    except Exception:
        pass

    return TopicDetail(
        id=row["id"],
        title=row["title"],
        category=row["category"],
        image_url=row.get("image_url"),
        view_count=row["view_count"],
        rank=row["rank"],
        created_at=row["created_at"],
        source_url=row.get("source_url", ""),
        body=row.get("body", ""),
        summary=summary,
        poll={
            "id": poll_data.get("id", ""),
            "topic_id": topic_id,
            "option_a_text": poll_data.get("option_a_text", "찬성"),
            "option_b_text": poll_data.get("option_b_text", "반대"),
            "option_a_count": poll_data.get("option_a_count", 0),
            "option_b_count": poll_data.get("option_b_count", 0),
            "user_voted": None,
        },
    )
