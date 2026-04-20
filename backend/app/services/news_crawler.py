"""뉴스 크롤러: knews-rss 기반 카테고리별 RSS 피드.

https://github.com/akngs/knews-rss 에서 선별한 피드를 사용합니다.

흐름:
  1. 카테고리별 RSS 피드 병렬 fetch
  2. XML 파싱 → 최신 기사 추출
  3. 중복 제거 후 카테고리당 상위 10개 반환
  4. 본문 fetch → CrawledPost 반환
"""
from __future__ import annotations

import asyncio
import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from bs4 import BeautifulSoup

from .crawler import CrawledPost, _HEADERS, _TIMEOUT, _fetch_page, _add_image, _unwrap_thumb, _is_content_image


# ---------------------------------------------------------------------------
# 카테고리별 RSS 피드 목록 (knews-rss 선별)
# 다양한 시각 확보를 위해 카테고리당 3~4개 언론사 혼합
# ---------------------------------------------------------------------------

_RSS_FEEDS: dict[str, list[tuple[str, str]]] = {
    "society": [
        ("경향신문", "https://www.khan.co.kr/rss/rssdata/society_news.xml"),
        ("한겨레", "https://www.hani.co.kr/rss/society/"),
        ("뉴시스", "https://newsis.com/RSS/society.xml"),
        ("동아일보", "https://rss.donga.com/national.xml"),
        ("조선일보", "https://www.chosun.com/arc/outboundfeeds/rss/category/national/?outputType=xml"),
    ],
    "economy": [
        ("경향신문", "https://www.khan.co.kr/rss/rssdata/economy_news.xml"),
        ("한겨레", "https://www.hani.co.kr/rss/economy/"),
        ("동아일보", "https://rss.donga.com/economy.xml"),
        ("조선일보", "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml"),
        ("뉴시스", "https://newsis.com/RSS/economy.xml"),
    ],
    "sports": [
        ("경향신문", "http://www.khan.co.kr/rss/rssdata/kh_sports.xml"),
        ("동아일보", "https://rss.donga.com/sports.xml"),
        ("뉴시스", "https://newsis.com/RSS/sports.xml"),
        ("조선일보", "https://www.chosun.com/arc/outboundfeeds/rss/category/sports/?outputType=xml"),
        ("한겨레", "https://www.hani.co.kr/rss/sports/"),
    ],
    "love": [  # 연예
        ("경향신문", "https://www.khan.co.kr/rss/rssdata/kh_entertainment.xml"),
        ("서울신문", "https://www.seoul.co.kr/xml/rss/rss_entertainment.xml"),
        ("뉴시스", "https://newsis.com/RSS/entertain.xml"),
        ("세계일보", "http://www.segye.com/Articles/RSSList/segye_entertainment.xml"),
        ("천지일보", "https://cdn.newscj.com/rss/gns_S1N15.xml"),
    ],
}

# 카테고리당 최종 반환할 기사 수
_MAX_PER_CATEGORY = 20


def _parse_pubdate(text: str) -> datetime:
    """RSS pubDate 문자열을 UTC datetime으로 변환합니다."""
    text = text.strip()
    try:
        # RFC 822 (Mon, 01 Jan 2024 00:00:00 +0900)
        return parsedate_to_datetime(text).astimezone(timezone.utc)
    except Exception:
        pass
    try:
        # ISO 8601 (2024-01-01T00:00:00+09:00)
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except Exception:
        pass
    return datetime.min.replace(tzinfo=timezone.utc)


def _make_ext_id(publisher: str, url: str, title: str) -> str:
    """중복 방지용 외부 ID를 생성합니다."""
    # URL 기반으로 숫자 ID 추출 시도
    match = re.search(r"/(\d{5,})", url)
    if match:
        return f"{publisher}_{match.group(1)}"
    # URL 해시 사용
    return f"{publisher}_{hashlib.md5(url.encode()).hexdigest()[:16]}"


async def _fetch_rss(
    client: httpx.AsyncClient,
    publisher: str,
    url: str,
    category: str,
) -> list[CrawledPost]:
    """단일 RSS 피드를 fetch하고 CrawledPost 리스트로 반환합니다."""
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return []

    try:
        soup = BeautifulSoup(resp.content, "lxml-xml")
    except Exception:
        try:
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            return []

    posts: list[CrawledPost] = []
    for item in soup.find_all("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pub_el = item.find("pubDate") or item.find("pubdate")

        title = title_el.get_text(strip=True) if title_el else ""
        # CDATA 또는 HTML 태그 제거 + HTML 엔티티 디코딩
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        if not title or len(title) < 5:
            continue

        # <link> 태그는 lxml-xml에서 next_sibling 방식으로 가져와야 할 때가 있음
        link = ""
        if link_el:
            link = link_el.get_text(strip=True) or link_el.get("href", "")
        if not link or not link.startswith("http"):
            continue

        desc = ""
        if desc_el:
            raw_desc = desc_el.get_text(strip=True)
            desc = html.unescape(re.sub(r"<[^>]+>", "", raw_desc))[:500]

        pub_dt = _parse_pubdate(pub_el.get_text(strip=True)) if pub_el else datetime.min.replace(tzinfo=timezone.utc)

        # RSS 피드에서 이미지 추출 시도
        # 1순위: <enclosure url="..." type="image/...">
        image_url: str | None = None
        enclosure = item.find("enclosure")
        if enclosure:
            enc_url = enclosure.get("url", "")
            enc_type = enclosure.get("type", "")
            if enc_url.startswith("http") and "image" in enc_type:
                image_url = enc_url

        # 2순위: <media:content> 또는 <media:thumbnail>
        if not image_url:
            for tag in ("media:content", "media:thumbnail", "content", "thumbnail"):
                el = item.find(tag)
                if el:
                    img = el.get("url", "")
                    if img.startswith("http"):
                        image_url = img
                        break

        # 3순위: description HTML 내 첫 번째 <img src="...">
        if not image_url and desc_el:
            raw_html = str(desc_el)
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)
            if img_match:
                img_src = img_match.group(1)
                if img_src.startswith("http"):
                    image_url = img_src

        ext_id = _make_ext_id(publisher, link, title)

        posts.append(CrawledPost(
            source="rss_news",
            external_id=ext_id,
            title=title,
            body=desc,
            url=link,
            category=category,  # type: ignore[arg-type]
            view_count=0,
            image_url=image_url,
            fetch_url=link,
        ))
        # pubDate를 메타데이터로 저장 (정렬용)
        posts[-1].__dict__["_pubdate"] = pub_dt

    return posts


async def crawl_news() -> list[CrawledPost]:
    """knews-rss 기반 카테고리별 뉴스 기사를 크롤링합니다."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 모든 피드 병렬 fetch
        tasks = []
        meta: list[tuple[str, str]] = []  # (category, publisher)
        for category, feeds in _RSS_FEEDS.items():
            for publisher, url in feeds:
                tasks.append(_fetch_rss(client, publisher, url, category))
                meta.append((category, publisher))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 카테고리별로 수집
        cat_posts: dict[str, list[CrawledPost]] = {cat: [] for cat in _RSS_FEEDS}
        for result in results:
            if not isinstance(result, list):
                continue
            for post in result:
                cat_posts[post.category].append(post)

        # 카테고리별 중복 제거 + 최신순 정렬 + 상위 N개
        final_posts: list[CrawledPost] = []
        for category, posts in cat_posts.items():
            seen_ids: set[str] = set()
            seen_titles: set[str] = set()
            unique: list[CrawledPost] = []
            for p in posts:
                if p.external_id in seen_ids:
                    continue
                # 제목 유사 중복 방지 (앞 20자 기준)
                title_key = re.sub(r"\s+", "", p.title[:20])
                if title_key in seen_titles:
                    continue
                seen_ids.add(p.external_id)
                seen_titles.add(title_key)
                unique.append(p)

            # pubDate 기준 최신순 정렬
            unique.sort(
                key=lambda p: p.__dict__.get("_pubdate", datetime.min.replace(tzinfo=timezone.utc)),
                reverse=True,
            )
            final_posts.extend(unique[:_MAX_PER_CATEGORY])

        # 본문 fetch (동시 5개 제한)
        sem = asyncio.Semaphore(5)

        async def fill_body(post: CrawledPost) -> None:
            # 본문과 이미지 모두 있으면 skip
            if post.image_url and post.body and len(post.body) > 150 and post.image_urls:
                return
            # 본문은 충분하지만 이미지가 없거나, 본문이 짧은 경우 → 페이지 fetch
            async with sem:
                body, fetched_images = await _fetch_page(client, post.url, "rss_news")
                if body and (not post.body or len(post.body) <= 150):
                    post.body = body
                # 대표 이미지 unwrap
                if post.image_url:
                    post.image_url = _unwrap_thumb(post.image_url)
                if fetched_images and not post.image_url:
                    post.image_url = fetched_images[0]
                # 전체 이미지 목록 구성 (중복 제거)
                all_imgs: list[str] = []
                if post.image_url and _is_content_image(post.image_url):
                    all_imgs.append(post.image_url)
                for img in fetched_images:
                    _add_image(img, all_imgs)
                if all_imgs:
                    post.image_urls = all_imgs[:10]

        await asyncio.gather(*[fill_body(p) for p in final_posts], return_exceptions=True)

    return final_posts
