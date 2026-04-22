"""Vercel Cron Job 전용 관리자 엔드포인트.

Vercel이 crons 설정으로 주기적으로 호출합니다.
x-admin-key 헤더로 무단 호출을 방지합니다.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

router = APIRouter()

_ADMIN_KEY = os.getenv("ADMIN_SECRET_KEY", "")


def _verify(x_admin_key: str | None) -> None:
    """Vercel Cron은 x-vercel-cron-signature 헤더를 보내지만,
    단순하게 우리 ADMIN_SECRET_KEY 헤더로도 허용합니다."""
    # Vercel Cron 자체 호출은 항상 허용 (VERCEL=1 환경)
    if os.getenv("VERCEL") == "1":
        return
    # 로컬에서 테스트 시 키 확인
    if _ADMIN_KEY and x_admin_key != _ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/debug-crawl")
async def debug_crawl(x_admin_key: str | None = Header(None)):
    """크롤러 결과를 DB 저장 없이 즉시 반환합니다 (디버깅용)."""
    _verify(x_admin_key)
    import asyncio
    from ..services.crawler import (
        PannCrawler, TheqooCrawler, InstizCrawler, TodayHumorCrawler,
        GaeddipCrawler, BobaedreamCrawler, MlbparkCrawler, DcinsideCrawler,
    )
    from ..services.news_crawler import crawl_news
    import httpx

    crawlers = [
        ("pann", PannCrawler()),
        ("theqoo", TheqooCrawler()),
        ("instiz", InstizCrawler()),
        ("todayhumor", TodayHumorCrawler()),
        ("gaeddip", GaeddipCrawler()),
        ("bobaedream", BobaedreamCrawler()),
        ("mlbpark", MlbparkCrawler()),
        ("dcinside", DcinsideCrawler()),
    ]

    from ..services.crawler import _HEADERS, _TIMEOUT

    async def _test_crawl(name, crawler, client):
        try:
            # HTTP 응답 먼저 테스트
            url = getattr(crawler, '_URL', None)
            http_status = None
            if url:
                try:
                    r = await client.get(url, headers=_HEADERS, timeout=_TIMEOUT)
                    http_status = r.status_code
                except Exception as e:
                    http_status = str(e)[:50]
            posts = await crawler.fetch(client)
            return name, posts, http_status
        except Exception as e:
            return name, [], str(e)[:100]

    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = await asyncio.gather(
            *[_test_crawl(name, c, client) for name, c in crawlers],
            return_exceptions=True,
        )

    breakdown = {}
    for result in results:
        if isinstance(result, Exception):
            breakdown["error"] = str(result)
        else:
            name, posts, http_status = result
            breakdown[name] = {
                "count": len(posts),
                "http_status": http_status,
                "sample": posts[0].title[:40] if posts else None,
            }

    news = await crawl_news()
    news_by_cat: dict[str, int] = {}
    for p in news:
        news_by_cat[p.category] = news_by_cat.get(p.category, 0) + 1

    return {
        "community_breakdown": breakdown,
        "news_by_category": news_by_cat,
        "news_total": len(news),
    }


@router.post("/ingest")
async def trigger_ingest(
    background_tasks: BackgroundTasks,
    x_admin_key: str | None = Header(None),
):
    """크롤링 + GPT 요약 + Supabase 저장 파이프라인을 백그라운드로 실행합니다."""
    _verify(x_admin_key)

    async def _run():
        from ..services.ingestion import run_ingestion
        import logging
        logger = logging.getLogger(__name__)
        try:
            result = await run_ingestion()
            logger.info("Manual ingest complete: %s", result)
        except Exception:
            logger.exception("Manual ingest failed")

    background_tasks.add_task(_run)
    return {"ok": True, "message": "ingestion started in background"}


@router.post("/rank")
async def trigger_rank(x_admin_key: str | None = Header(None)):
    """토픽 랭킹을 재계산합니다."""
    _verify(x_admin_key)
    from ..services.ranking import recompute_ranks
    await recompute_ranks()
    return {"ok": True}


@router.post("/reset")
async def reset_topics(x_admin_key: str | None = Header(None)):
    """모든 토픽·투표·포인트 트랜잭션을 삭제합니다 (재인제스션 전 초기화용)."""
    _verify(x_admin_key)
    from ..database import db
    client = db()
    client.table("polls").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    client.table("topics").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    return {"ok": True, "message": "모든 토픽/투표 삭제 완료"}


@router.post("/backfill-bodies")
async def backfill_bodies(
    background_tasks: BackgroundTasks,
    x_admin_key: str | None = Header(None),
):
    """body가 비어 있는 기존 토픽들의 본문을 크롤링해서 채웁니다."""
    _verify(x_admin_key)

    async def _run():
        import asyncio
        import logging
        import httpx
        from ..database import db
        from ..services.crawler import _fetch_page

        logger = logging.getLogger(__name__)
        client = db()

        # body가 없거나 빈 토픽 조회
        res = client.table("topics").select("id, source_url, source").eq("body", "").limit(50).execute()
        rows = res.data or []
        if not rows:
            # None 또는 공백인 경우도 처리
            res2 = client.table("topics").select("id, source_url, source").is_("body", "null").limit(50).execute()
            rows = res2.data or []

        if not rows:
            logger.info("backfill-bodies: 빈 body 토픽 없음")
            return

        logger.info("backfill-bodies: %d개 토픽 본문 채우기 시작", len(rows))
        sem = asyncio.Semaphore(5)

        async def fill(row: dict) -> None:
            url = row.get("source_url", "")
            if not url:
                return
            source = row.get("source", "naver_news")
            # source 컬럼이 있으면 그대로 사용, 없으면 source_url로 추정
            if not source or source == "naver_news":
                if "pann.nate" in url:
                    source = "pann"
                elif "theqoo.net" in url:
                    source = "theqoo"
                elif "instiz.net" in url:
                    source = "instiz"
                elif "todayhumor.co.kr" in url:
                    source = "todayhumor"
                elif "gaeddip.com" in url:
                    source = "gaeddip"
                elif "bobaedream.co.kr" in url:
                    source = "bobaedream"
                elif "mlbpark.com" in url:
                    source = "mlbpark"
                elif "dcinside.com" in url:
                    source = "dcinside"
                elif "news.naver.com" in url or "n.news.naver.com" in url:
                    source = "naver_news"

            async with sem:
                try:
                    async with httpx.AsyncClient(follow_redirects=True) as c:
                        body, image_url = await _fetch_page(c, url, source)
                except Exception:
                    return

            if not body:
                return

            update_data: dict = {"body": body}
            if image_url:
                update_data["image_url"] = image_url

            try:
                client.table("topics").update(update_data).eq("id", row["id"]).execute()
                logger.info("backfill-bodies: topic %s 완료 (body %d자)", row["id"], len(body))
            except Exception as e:
                logger.error("backfill-bodies: topic %s 업데이트 실패: %s", row["id"], e)

        await asyncio.gather(*[fill(r) for r in rows], return_exceptions=True)
        logger.info("backfill-bodies: 완료")

    background_tasks.add_task(_run)
    return {"ok": True, "message": f"본문 백필 시작 (최대 50개)"}


@router.post("/backfill-images")
async def backfill_images(
    background_tasks: BackgroundTasks,
    x_admin_key: str | None = Header(None),
):
    """기존 토픽들의 image_urls_json을 최신 크롤링 로직으로 다시 채웁니다."""
    _verify(x_admin_key)

    async def _run():
        import asyncio
        import json
        import logging
        import httpx
        from ..database import db
        from ..services.crawler import _fetch_page, _normalize_url, _unwrap_thumb, _add_image, _is_content_image

        logger = logging.getLogger(__name__)
        client = db()

        # 전체 토픽 조회 (최대 200개)
        res = client.table("topics").select("id, source, source_url, image_url").limit(200).execute()
        rows = res.data or []
        logger.info("backfill-images: %d개 토픽 이미지 재수집 시작", len(rows))

        sem = asyncio.Semaphore(5)

        async def fill(row: dict) -> None:
            url = row.get("source_url", "")
            source = row.get("source", "naver_news")
            if not url:
                return
            async with sem:
                try:
                    async with httpx.AsyncClient(follow_redirects=True) as c:
                        _body, fetched_images = await _fetch_page(c, url, source)
                except Exception:
                    return

            # 대표 이미지 정규화 (http→https 포함)
            raw_image_url = row.get("image_url") or ""
            image_url = _normalize_url(_unwrap_thumb(raw_image_url)) if raw_image_url else None

            all_imgs: list[str] = []
            if image_url:
                _add_image(image_url, all_imgs)  # 중복 제거 기준 통일
            for img in fetched_images:
                _add_image(img, all_imgs)

            # 아이콘/로고 등 비콘텐츠 이미지가 image_url에 있으면 정리
            final_image_url: str | None = image_url if (image_url and _is_content_image(image_url)) else (all_imgs[0] if all_imgs else None)

            update_data: dict = {
                "image_urls_json": json.dumps(all_imgs[:10], ensure_ascii=False) if all_imgs else None,
                "image_url": final_image_url,
            }

            try:
                client.table("topics").update(update_data).eq("id", row["id"]).execute()
            except Exception as e:
                logger.error("backfill-images: topic %s 실패: %s", row["id"], e)

        await asyncio.gather(*[fill(r) for r in rows], return_exceptions=True)
        logger.info("backfill-images: 완료")

    background_tasks.add_task(_run)
    return {"ok": True, "message": "이미지 백필 시작 (최대 200개)"}


@router.post("/refresh-source-bodies")
async def refresh_source_bodies(
    background_tasks: BackgroundTasks,
    source: str = "segye",
    x_admin_key: str | None = Header(None),
):
    """특정 소스 토픽들의 body·image_urls를 강제로 다시 크롤링합니다 (기존 내용 덮어씀)."""
    _verify(x_admin_key)

    async def _run():
        import asyncio
        import json
        import logging
        import httpx
        from ..database import db
        from ..services.crawler import _fetch_page

        logger = logging.getLogger(__name__)
        client = db()

        res = client.table("topics").select("id, source_url, source").eq("source", source).limit(100).execute()
        rows = res.data or []
        logger.info("refresh-source-bodies: %s 토픽 %d개 재수집 시작", source, len(rows))

        sem = asyncio.Semaphore(3)

        async def refresh(row: dict) -> None:
            url = row.get("source_url", "")
            src = row.get("source", source)
            if not url:
                return
            async with sem:
                try:
                    async with httpx.AsyncClient(follow_redirects=True) as c:
                        body, images = await _fetch_page(c, url, src)
                except Exception as e:
                    logger.error("refresh: %s 실패: %s", url, e)
                    return

            if not body and not images:
                return

            update: dict = {}
            if body:
                update["body"] = body
            if images:
                update["image_urls_json"] = json.dumps(images, ensure_ascii=False)
                update["image_url"] = images[0]

            try:
                client.table("topics").update(update).eq("id", row["id"]).execute()
                logger.info("refresh: %s 완료 (body %d자, 이미지 %d개)", row["id"], len(body), len(images))
            except Exception as e:
                logger.error("refresh: %s 업데이트 실패: %s", row["id"], e)

        await asyncio.gather(*[refresh(r) for r in rows], return_exceptions=True)
        logger.info("refresh-source-bodies: 완료")

    background_tasks.add_task(_run)
    return {"ok": True, "message": f"{source} 토픽 body 재수집 시작"}


@router.post("/fix-categories")
async def fix_categories(x_admin_key: str | None = Header(None)):
    """뉴스 토픽의 카테고리를 키워드 기반으로 재분류합니다.
    story 카테고리는 건드리지 않고, 뉴스(society/economy/sports/love) 기사만 대상으로 합니다."""
    _verify(x_admin_key)
    from ..database import db
    from ..services.crawler import _guess_category_from_title

    client = db()
    # 뉴스 카테고리 토픽만 조회
    res = client.table("topics").select("id, title, category").in_(
        "category", ["society", "economy", "sports", "love"]
    ).execute()
    rows = res.data or []

    fixed = 0
    for row in rows:
        guessed = _guess_category_from_title(row["title"])
        if guessed == "story":
            # 키워드 없음 → society로 fallback (뉴스 기사)
            new_cat = "society"
        else:
            new_cat = guessed

        if new_cat != row["category"]:
            client.table("topics").update({"category": new_cat}).eq("id", row["id"]).execute()
            fixed += 1

    # 랭킹 재계산
    from ..services.ranking import recompute_ranks
    await recompute_ranks()

    return {"ok": True, "fixed": fixed, "total": len(rows)}
