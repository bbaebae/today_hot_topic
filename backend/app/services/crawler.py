"""커뮤니티/뉴스 크롤러.

소스:
  - 썰(story):   네이트판 베스트, 루리웹 베스트, 펨코 베스트
  - 사회(society): 네이버 뉴스 사회 랭킹
  - 경제(economy): 네이버 뉴스 경제 랭킹
  - 스포츠(sports): 네이버 뉴스 스포츠 랭킹
  - 연애(love):   네이버 뉴스 연예 랭킹
"""
from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

from ..schemas.topic import Category

# Vercel 서버리스 환경에서는 Playwright(Chromium) 사용 불가 (바이너리 용량 초과)
_PLAYWRIGHT_AVAILABLE = os.getenv("VERCEL") != "1"
try:
    if _PLAYWRIGHT_AVAILABLE:
        from playwright.async_api import async_playwright
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}
_TIMEOUT = httpx.Timeout(15.0)


@dataclass
class CrawledPost:
    source: str
    external_id: str
    title: str
    body: str
    url: str
    category: Category
    image_url: str | None = None
    view_count: int = 0


# ---------------------------------------------------------------------------
# 네이트판 베스트 (썰)
# ---------------------------------------------------------------------------

class PannCrawler:
    _BASE = "https://pann.nate.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            resp = await client.get(self._BASE + "/", headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        for a in soup.select("div.bestTalkBox a[href*='/talk/']"):
            href = a.get("href", "")
            if "/channel/" in href or "#" in href:
                continue
            if not href.startswith("http"):
                href = self._BASE + href

            match = re.search(r"/talk/(\d+)", href)
            if not match:
                continue
            ext_id = match.group(1)
            if ext_id in seen:
                continue
            seen.add(ext_id)

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            posts.append(CrawledPost(
                source="pann",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
            ))
            if len(posts) >= 15:
                break

        return posts


# ---------------------------------------------------------------------------
# 루리웹 유머 베스트 (썰)
# ---------------------------------------------------------------------------

class RuliwebCrawler:
    _URL = "https://bbs.ruliweb.com/best/board/300143"
    _BASE = "https://bbs.ruliweb.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            resp = await client.get(self._URL, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []

        for a in soup.select("table.board_list_table tr td.subject a.deco"):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            match = re.search(r"/read/(\d+)", href)
            ext_id = match.group(1) if match else re.sub(r"[^\w]", "", href)[-20:]

            if not href.startswith("http"):
                href = self._BASE + href

            posts.append(CrawledPost(
                source="ruliweb",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
            ))
            if len(posts) >= 15:
                break

        return posts


# ---------------------------------------------------------------------------
# 펨코 베스트 (썰) — Playwright 헤드리스 브라우저
# ---------------------------------------------------------------------------

class FmkoreaCrawler:
    _URL = "https://www.fmkorea.com/best"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        if not _PLAYWRIGHT_AVAILABLE:
            return []  # Vercel 환경에서는 스킵
        try:
            async with async_playwright() as p:  # type: ignore[name-defined]
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(self._URL, timeout=20000)
                await page.wait_for_timeout(2000)
                html = await page.content()
                await browser.close()
        except Exception:
            return []

        soup = BeautifulSoup(html, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        for a in soup.select("a"):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            # 공지/자료 글 제외
            if re.match(r"^\[통합\]|\[20\d\d자료", title):
                continue
            match = re.search(r"/(\d{9,})", href)
            if not match:
                continue
            ext_id = match.group(1)
            if ext_id in seen:
                continue
            seen.add(ext_id)

            full_url = href if href.startswith("http") else f"https://www.fmkorea.com{href}"
            posts.append(CrawledPost(
                source="fmkorea",
                external_id=ext_id,
                title=title,
                body="",
                url=full_url,
                category=_guess_category_from_title(title),
            ))
            if len(posts) >= 15:
                break

        return posts


# ---------------------------------------------------------------------------
# 네이버 뉴스 랭킹 (사회 / 경제 / 스포츠 / 연예)
# ---------------------------------------------------------------------------

class NaverNewsRankingCrawler:
    # sid1: 101=경제, 102=사회, 106=연예, 107=스포츠
    _URLS: list[tuple[str, str]] = [
        ("society", "https://news.naver.com/main/ranking/popularDay.naver?sid1=102"),
        ("economy", "https://news.naver.com/main/ranking/popularDay.naver?sid1=101"),
        ("sports",  "https://news.naver.com/main/ranking/popularDay.naver?sid1=107"),
        ("love",    "https://news.naver.com/main/ranking/popularDay.naver?sid1=106"),
    ]

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        posts: list[CrawledPost] = []
        for category, url in self._URLS:
            try:
                resp = await client.get(url, headers=_HEADERS, timeout=_TIMEOUT)
                resp.raise_for_status()
            except httpx.HTTPError:
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            seen: set[str] = set()
            count = 0

            for a in soup.select("div.rankingnews_box a.list_title"):
                href = a.get("href", "")
                title = a.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                match = re.search(r"article/(\d+/\d+)", href)
                ext_id = match.group(1).replace("/", "_") if match else re.sub(r"[^\w]", "", href)[-30:]
                if ext_id in seen:
                    continue
                seen.add(ext_id)

                if not href.startswith("http"):
                    href = "https://news.naver.com" + href

                posts.append(CrawledPost(
                    source="naver_news",
                    external_id=ext_id,
                    title=title,
                    body="",
                    url=href,
                    category=category,  # type: ignore[arg-type]
                ))
                count += 1
                if count >= 10:
                    break

        return posts


# ---------------------------------------------------------------------------
# 전체 크롤링 실행
# ---------------------------------------------------------------------------

async def crawl_all() -> list[CrawledPost]:
    # FmkoreaCrawler는 Playwright 의존으로 메모리 과다 사용 → 제외
    crawlers = [PannCrawler(), RuliwebCrawler(), NaverNewsRankingCrawler()]
    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = await asyncio.gather(
            *[c.fetch(client) for c in crawlers],
            return_exceptions=True,
        )

    posts: list[CrawledPost] = []
    for r in results:
        if isinstance(r, list):
            posts.extend(r)
    return posts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ECONOMY_KEYWORDS = re.compile(
    r"주식|코스피|나스닥|비트코인|환율|금리|부동산|아파트|ETF|펀드|채권|달러|경제|물가|증시|코인|투자|적금|통장", re.IGNORECASE
)
_SOCIETY_KEYWORDS = re.compile(
    r"정치|대통령|국회|선거|사건|사고|범죄|경찰|법원|외교|전쟁|군사|정부|판결|시위|파업", re.IGNORECASE
)
_SPORTS_KEYWORDS = re.compile(
    r"손흥민|이강인|류현진|박지성|야구|축구|농구|배구|골프|올림픽|월드컵|KBO|EPL|NBA|스포츠|득점|우승", re.IGNORECASE
)
_LOVE_KEYWORDS = re.compile(
    r"연예인|아이돌|배우|가수|드라마|영화|열애|결별|결혼|이혼|연애|폭로|스캔들|엔터|팬", re.IGNORECASE
)


def _guess_category_from_title(title: str) -> Category:
    if _ECONOMY_KEYWORDS.search(title):
        return "economy"
    if _SPORTS_KEYWORDS.search(title):
        return "sports"
    if _LOVE_KEYWORDS.search(title):
        return "love"
    if _SOCIETY_KEYWORDS.search(title):
        return "society"
    return "story"


def _parse_count(text: str) -> int:
    text = text.replace(",", "").strip()
    if "만" in text:
        try:
            return int(float(text.replace("만", "")) * 10000)
        except ValueError:
            return 0
    try:
        return int(re.sub(r"[^\d]", "", text) or "0")
    except ValueError:
        return 0
