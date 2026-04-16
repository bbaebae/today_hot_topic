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

    _SELECT = "id, title, category, image_url, view_count, rank, created_at, polls(id, option_a_text, option_b_text)"

    if category:
        res = (
            client.table("topics")
            .select(_SELECT)
            .eq("category", category)
            .order("rank")
            .limit(50)
            .execute()
        )
        topics = res.data or []

        if not topics:
            res = (
                client.table("topics")
                .select(_SELECT)
                .order("created_at", desc=True)
                .limit(30)
                .execute()
            )
            topics = res.data or []
    else:
        res = (
            client.table("topics")
            .select(_SELECT)
            .order("view_count", desc=True)
            .limit(50)
            .execute()
        )
        topics = res.data or []

    items = []
    for row in topics:
        poll_list = row.pop("polls", None) or []
        poll = poll_list[0] if poll_list else {}
        items.append(TopicListItem(
            **row,
            poll_id=poll.get("id", ""),
            poll_option_a=poll.get("option_a_text", ""),
            poll_option_b=poll.get("option_b_text", ""),
        ))
    return TopicsResponse(topics=items)


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
