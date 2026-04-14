"""토픽 랭킹 계산 및 Supabase 업데이트.

점수 공식:
  score = view_count * recency_factor + (option_a_count + option_b_count) * 2

  recency_factor = 1 / (1 + hours_since_created / 12)
  → 12시간 전 글은 점수가 절반으로 감소
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from ..database import db
from ..schemas.topic import Category


def _recency_factor(created_at_str: str) -> float:
    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
        return 1 / (1 + hours / 12)
    except Exception:
        return 0.5


def _score(row: dict[str, Any]) -> float:
    view_count: int = row.get("view_count", 0)
    votes: int = row.get("total_votes", 0)
    rf = _recency_factor(row.get("created_at", ""))
    return view_count * rf + votes * 2


async def recompute_ranks(category: Category | None = None) -> None:
    """카테고리별 또는 전체 토픽 랭킹을 재계산하고 DB에 반영합니다."""
    client = db()

    query = client.table("topics").select(
        "id, category, view_count, created_at"
    )
    if category:
        query = query.eq("category", category)

    res = query.execute()
    topics = res.data or []

    # poll 투표 수 조인
    poll_res = client.table("polls").select("topic_id, option_a_count, option_b_count").execute()
    vote_map: dict[str, int] = {
        row["topic_id"]: row["option_a_count"] + row["option_b_count"]
        for row in (poll_res.data or [])
    }
    for t in topics:
        t["total_votes"] = vote_map.get(t["id"], 0)

    # 카테고리별로 그룹화하여 순위 계산
    from itertools import groupby

    all_categories: list[Category] = ["story", "society", "economy", "sports", "love"]
    for cat in all_categories:
        cat_topics = [t for t in topics if t["category"] == cat]
        cat_topics.sort(key=_score, reverse=True)
        updates = []
        for rank, t in enumerate(cat_topics, start=1):
            updates.append({"id": t["id"], "rank": rank})
        for upd in updates:
            client.table("topics").update({"rank": upd["rank"]}).eq("id", upd["id"]).execute()
