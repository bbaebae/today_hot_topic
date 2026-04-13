from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..database import db
from ..schemas.topic import TopicDetail, TopicListItem, TopicsResponse

router = APIRouter()

Category = Literal["news", "story", "finance"]


@router.get("", response_model=TopicsResponse)
async def list_topics(
    category: Category | None = Query(None, description="뉴스/썰/금융 필터"),
):
    client = db()
    query = client.table("topics").select(
        "id, title, category, image_url, view_count, rank, created_at"
    )
    if category:
        query = query.eq("category", category).order("rank")
    else:
        query = query.order("view_count", desc=True)

    res = query.limit(50).execute()
    topics = [TopicListItem(**row) for row in (res.data or [])]
    return TopicsResponse(topics=topics)


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
    # summary is stored as a JSON array string in Supabase
    raw_summary = row.get("summary_json") or "[]"
    summary: list[str] = json.loads(raw_summary) if isinstance(raw_summary, str) else raw_summary

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
