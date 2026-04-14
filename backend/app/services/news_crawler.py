"""뉴스 크롤러: 다음 실시간 이슈 키워드 → 네이버 뉴스 검색 API.

흐름:
  1. 다음 실시간 이슈 페이지 스크래핑 → 트렌딩 키워드 상위 10개
  2. 각 키워드로 네이버 뉴스 검색 API 호출 → 대표 기사 1개
  3. CrawledPost(category="news") 로 반환
"""
from __future__ import annotations

import asyncio
import re
import urllib.parse

import httpx
from bs4 import BeautifulSoup

from .crawler import CrawledPost, _HEADERS, _TIMEOUT

_DAUM_REALTIME_URL = "https://www.daum.net/"
_NAVER_NEWS_API = "https://openapi.naver.com/v1/search/news.json"


async def _fetch_daum_trending(client: httpx.AsyncClient) -> list[str]:
    """다음 메인에서 실시간 이슈 키워드를 추출합니다."""
    try:
        resp = await client.get(_DAUM_REALTIME_URL, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except httpx.HTTPError:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    keywords: list[str] = []

    # 다음 실시간 이슈 섹션
    for el in soup.select(
        "div.realtime_part a, ol.list_realtime a, ul.list_issue a, "
        "div#mArticle a.link_txt, div.wrap_issue a"
    ):
        text = el.get_text(strip=True)
        # 순위 번호 제거 (예: "1위 카리나")
        text = re.sub(r"^\d+\s*위?\s*", "", text).strip()
        if text and len(text) >= 2 and text not in keywords:
            keywords.append(text)
        if len(keywords) >= 10:
            break

    return keywords


async def _search_naver_news(
    client: httpx.AsyncClient,
    keyword: str,
    naver_client_id: str,
    naver_client_secret: str,
) -> CrawledPost | None:
    """네이버 뉴스 검색 API로 키워드 관련 대표 기사를 가져옵니다."""
    params = {
        "query": keyword,
        "display": 3,
        "sort": "date",
    }
    headers = {
        **_HEADERS,
        "X-Naver-Client-Id": naver_client_id,
        "X-Naver-Client-Secret": naver_client_secret,
    }
    try:
        resp = await client.get(
            _NAVER_NEWS_API,
            params=params,
            headers=headers,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    data = resp.json()
    items = data.get("items", [])
    if not items:
        return None

    # 가장 최신 기사 사용
    item = items[0]
    title = _strip_html(item.get("title", keyword))
    description = _strip_html(item.get("description", ""))
    link = item.get("originallink") or item.get("link", "")

    # 외부 ID: URL에서 추출하거나 title 해시 사용
    ext_id = re.sub(r"[^\w]", "", link)[-40:] or re.sub(r"[^\w]", "", title)[:40]

    from .crawler import _guess_category_from_title
    category = _guess_category_from_title(title)

    return CrawledPost(
        source="naver_api",
        external_id=ext_id,
        title=title,
        body=description,
        url=link,
        category=category,
        view_count=0,
    )


def _strip_html(text: str) -> str:
    """네이버 API가 반환하는 <b> 등 HTML 태그를 제거합니다."""
    return re.sub(r"<[^>]+>", "", text).strip()


async def crawl_news() -> list[CrawledPost]:
    """다음 트렌딩 키워드 기반 뉴스 기사를 크롤링합니다."""
    from ..config import settings

    async with httpx.AsyncClient() as client:
        keywords = await _fetch_daum_trending(client)
        if not keywords:
            return []

        tasks = [
            _search_naver_news(
                client,
                kw,
                settings.naver_client_id,
                settings.naver_client_secret,
            )
            for kw in keywords
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    posts = [r for r in results if isinstance(r, CrawledPost)]
    return posts
