from __future__ import annotations

import json
import re
import time
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query

from ..database import db
from ..schemas.topic import TopicDetail, TopicListItem, TopicsResponse

router = APIRouter()

# 인메모리 캐시: 카테고리별 (데이터, 타임스탬프)
_list_cache: dict[str, tuple[float, TopicsResponse]] = {}
_LIST_CACHE_TTL = 60  # 1분

# DB에 이미 저장된 기사 본문도 실시간 정제 (크롤러 패턴 변경 전 저장된 데이터 커버)
_BODY_JUNK_PATTERNS = [
    re.compile(r'KH_View_\w+\s*\[(?:pc|m)-AD\]'),
    re.compile(r'^\s*//\s*\[(?:pc|m)-AD\]'),
    re.compile(r'\[(?:pc|m)-AD\]\s*[\w\s]*(배너|광고)\s*\(\d+x\d+\)'),
    re.compile(r'^\s*\[s\].*?\[e\]', re.DOTALL),
    re.compile(r'^\s*바이라인\s*$'),
    re.compile(r'AD\s*Manager\s*\|\s*AD\d+'),
    re.compile(r'^\s*//\s*AD\s*Manager'),
    re.compile(r'PC 기사뷰 본문.*?수정\)'),
    re.compile(r'<\s*(iframe|script|ins)\b[^>]*>'),
    re.compile(r'</(iframe|script|ins)>'),
    re.compile(r'^\s*(width|height|frameborder|scrolling|topmargin|marginwidth)='),
    re.compile(r'src="//adex\.|src=\'//adex\.'),
    re.compile(r'referrerpolicy='),
]


def _clean_body(text: str) -> str:
    """DB에 저장된 기사 본문을 응답 전 실시간 정제합니다."""
    lines = text.split('\n')
    cleaned = [line for line in lines if not any(p.search(line.strip()) for p in _BODY_JUNK_PATTERNS)]
    return '\n'.join(cleaned).strip()

Category = Literal["story", "society", "economy", "sports", "love"]


@router.get("", response_model=TopicsResponse)
async def list_topics(
    category: Category | None = Query(None, description="썰/사회/경제/스포츠/연애 필터"),
):
    cache_key = category or "all"
    cached = _list_cache.get(cache_key)
    if cached and time.time() - cached[0] < _LIST_CACHE_TTL:
        return cached[1]

    client = db()

    _SELECT = "id, title, category, image_url, view_count, rank, created_at"

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

    if not topics:
        return TopicsResponse(topics=[])

    # polls 별도 쿼리
    topic_ids = [row["id"] for row in topics]
    polls_res = (
        client.table("polls")
        .select("id, topic_id, option_a_text, option_b_text")
        .in_("topic_id", topic_ids)
        .execute()
    )
    polls_map = {p["topic_id"]: p for p in (polls_res.data or [])}

    items = []
    for row in topics:
        poll = polls_map.get(row["id"], {})
        # http→https 정규화
        img = row.get("image_url")
        if img and img.startswith("http://"):
            row = {**row, "image_url": "https://" + img[7:]}
        items.append(TopicListItem(
            **row,
            poll_id=poll.get("id", ""),
            poll_option_a=poll.get("option_a_text", ""),
            poll_option_b=poll.get("option_b_text", ""),
        ))
    result = TopicsResponse(topics=items)
    _list_cache[cache_key] = (time.time(), result)
    return result


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

    # top_comments_json 파싱
    raw_comments = row.get("top_comments_json") or "[]"
    try:
        top_comments: list[str] = json.loads(raw_comments) if isinstance(raw_comments, str) else []
        if not isinstance(top_comments, list):
            top_comments = []
    except (json.JSONDecodeError, TypeError):
        top_comments = []

    # image_urls_json 파싱 + http→https 정규화 + 중복 제거
    raw_image_urls = row.get("image_urls_json") or "[]"
    try:
        _parsed_urls: list[str] = json.loads(raw_image_urls) if isinstance(raw_image_urls, str) else []
        if not isinstance(_parsed_urls, list):
            _parsed_urls = []
    except (json.JSONDecodeError, TypeError):
        _parsed_urls = []
    # http://를 https://로 통일하고 중복 제거
    image_urls: list[str] = []
    seen_urls: set[str] = set()
    for _u in _parsed_urls:
        _u = _u.replace("http://", "https://", 1) if _u.startswith("http://") else _u
        if _u not in seen_urls:
            seen_urls.add(_u)
            image_urls.append(_u)

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

    _img_url = row.get("image_url")
    if _img_url and _img_url.startswith("http://"):
        _img_url = "https://" + _img_url[7:]

    raw_body = row.get("body") or ""
    cleaned_body = _clean_body(raw_body) if raw_body else ""

    return TopicDetail(
        id=row["id"],
        title=row["title"],
        category=row["category"],
        image_url=_img_url,
        image_urls=image_urls,
        view_count=row["view_count"],
        rank=row["rank"],
        created_at=row["created_at"],
        source_url=row.get("source_url", ""),
        body=cleaned_body,
        summary=summary,
        top_comments=top_comments,
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
