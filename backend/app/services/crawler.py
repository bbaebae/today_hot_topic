"""커뮤니티/뉴스 크롤러.

소스:
  - 썰: 네이트판 베스트, 루리웹 베스트
  - 뉴스: 네이버 뉴스 랭킹
  - 금융: 네이버 뉴스 경제 랭킹
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from ..schemas.topic import Category

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
        try:
            async with async_playwright() as p:
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
# 네이버 뉴스 랭킹 (뉴스 + 금융)
# ---------------------------------------------------------------------------

class NaverNewsRankingCrawler:
    # sid: 100=정치, 101=경제, 102=사회, 103=생활/문화, 104=세계, 105=IT
    _URLS = {
        "news": "https://news.naver.com/main/ranking/popularDay.naver",
        "finance": "https://news.naver.com/main/ranking/popularDay.naver?sid1=101",
    }

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        posts: list[CrawledPost] = []
        for category, url in self._URLS.items():
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
    crawlers = [PannCrawler(), RuliwebCrawler(), FmkoreaCrawler(), NaverNewsRankingCrawler()]
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

_FINANCE_KEYWORDS = re.compile(
    r"주식|코스피|나스닥|비트코인|환율|금리|부동산|아파트|ETF|펀드|채권|달러|경제|물가|증시", re.IGNORECASE
)
_NEWS_KEYWORDS = re.compile(
    r"정치|대통령|국회|선거|뉴스|사건|사고|범죄|경찰|법원|외교|전쟁|군사|정부|판결", re.IGNORECASE
)


def _guess_category_from_title(title: str) -> Category:
    if _FINANCE_KEYWORDS.search(title):
        return "finance"
    if _NEWS_KEYWORDS.search(title):
        return "news"
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
