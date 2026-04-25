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
import random
import uuid
from datetime import datetime, timezone

from .crawler import CrawledPost, crawl_all
from .news_crawler import crawl_news
from .summarizer import summarize
from .ranking import recompute_ranks
from ..database import db
from ..schemas.topic import Category


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

    # GPT-4o 요약 + 투표 선택지 생성 (최대 5개 동시 처리)
    semaphore = asyncio.Semaphore(5)

    async def summarize_with_limit(post: CrawledPost) -> tuple[list[str], tuple[str, str]]:
        async with semaphore:
            return await summarize(
                post.title, post.body, post.category,
                post.image_urls or None,
                post.top_comments or None,
            )

    results = await asyncio.gather(*[summarize_with_limit(p) for p in new_posts])

    # Supabase 저장
    now = datetime.now(timezone.utc).isoformat()
    for post, (summary_lines, poll_opts) in zip(new_posts, results):
        topic_id = str(uuid.uuid4())
        poll_id = str(uuid.uuid4())

        opt_a, opt_b = poll_opts

        client.table("topics").upsert(
            {
                "id": topic_id,
                "title": post.title,
                "category": post.category,
                "source": post.source,
                "external_id": post.external_id,
                "source_url": post.url,
                "image_url": post.image_url,
                "image_urls_json": json.dumps(post.image_urls, ensure_ascii=False) if post.image_urls else None,
                "top_comments_json": json.dumps(post.top_comments, ensure_ascii=False) if post.top_comments else None,
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

        # 초기 참여자 시드 (10~20명, 랜덤 비율)
        seed_total = random.randint(10, 20)
        a_ratio = random.uniform(0.3, 0.7)
        seed_a = round(seed_total * a_ratio)
        seed_b = seed_total - seed_a

        client.table("polls").upsert(
            {
                "id": poll_id,
                "topic_id": actual_topic_id,
                "option_a_text": opt_a,
                "option_b_text": opt_b,
                "option_a_count": seed_a,
                "option_b_count": seed_b,
                "created_at": now,
            },
            on_conflict="topic_id",
            ignore_duplicates=True,
        ).execute()

    # 랭킹 재계산
    await recompute_ranks()

    return {"crawled": len(posts), "new": len(new_posts)}
