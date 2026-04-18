"""크롤링 → GPT-4o 요약 → Supabase 저장 파이프라인.

흐름:
  1. crawler.crawl_all() → CrawledPost 리스트
  2. 중복 체크 (source + external_id 기준)
  3. 신규 글만 summarizer.summarize() 호출
  4. 기본 찬반 투표 옵션 생성
  5. topics + polls 테이블에 upsert
  6. ranking.recompute_ranks() 실행
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from .crawler import CrawledPost, crawl_all
from .news_crawler import crawl_news
from .summarizer import summarize
from .ranking import recompute_ranks
from ..database import db
from ..schemas.topic import Category


_DEFAULT_POLL_OPTIONS: dict[Category, tuple[str, str]] = {
    "story":   ("공감해요", "공감 안 해요"),
    "society": ("사실이다", "과장된 것 같다"),
    "economy": ("오를 것 같다", "내릴 것 같다"),
    "sports":  ("잘할 것 같다", "못할 것 같다"),
    "love":    ("이해해요", "이해 못하겠어요"),
}


async def run_ingestion() -> dict[str, int]:
    """전체 파이프라인을 실행하고 저장된 신규 토픽 수를 반환합니다."""
    community_posts, news_posts = await asyncio.gather(crawl_all(), crawl_news())
    posts = community_posts + news_posts
    if not posts:
        return {"crawled": 0, "new": 0}

    client = db()

    # 중복 체크용 existing set
    existing_res = client.table("topics").select("source, external_id").execute()
    existing_keys = {
        (row["source"], row["external_id"])
        for row in (existing_res.data or [])
    }

    new_posts = [
        p for p in posts
        if (p.source, p.external_id) not in existing_keys
    ]

    if not new_posts:
        return {"crawled": len(posts), "new": 0}

    # GPT-4o 요약 (최대 5개 동시 처리)
    semaphore = asyncio.Semaphore(5)

    async def summarize_with_limit(post: CrawledPost) -> list[str]:
        async with semaphore:
            return await summarize(post.title, post.body)

    summaries = await asyncio.gather(*[summarize_with_limit(p) for p in new_posts])

    # Supabase 저장
    now = datetime.now(timezone.utc).isoformat()
    for post, summary_lines in zip(new_posts, summaries):
        topic_id = str(uuid.uuid4())
        poll_id = str(uuid.uuid4())

        opt_a, opt_b = _DEFAULT_POLL_OPTIONS.get(post.category, ("찬성", "반대"))

        client.table("topics").upsert(
            {
                "id": topic_id,
                "title": post.title,
                "category": post.category,
                "source": post.source,
                "external_id": post.external_id,
                "source_url": post.url,
                "image_url": post.image_url,
                "view_count": min(post.view_count, 2_000_000_000),
                "rank": 9999,
                "body": post.body,
                "summary_json": json.dumps(summary_lines, ensure_ascii=False),
                "created_at": now,
            },
            on_conflict="source,external_id",
            ignore_duplicates=True,
        ).execute()

        # 실제 저장된 topic_id 조회 (중복 시 기존 ID 사용)
        existing = (
            client.table("topics")
            .select("id")
            .eq("source", post.source)
            .eq("external_id", post.external_id)
            .maybe_single()
            .execute()
        )
        actual_topic_id = existing.data["id"] if existing.data else topic_id

        client.table("polls").upsert(
            {
                "id": poll_id,
                "topic_id": actual_topic_id,
                "option_a_text": opt_a,
                "option_b_text": opt_b,
                "option_a_count": 0,
                "option_b_count": 0,
                "created_at": now,
            },
            on_conflict="topic_id",
            ignore_duplicates=True,
        ).execute()

    # 랭킹 재계산
    await recompute_ranks()

    return {"crawled": len(posts), "new": len(new_posts)}
