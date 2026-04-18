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
_BODY_TIMEOUT = httpx.Timeout(10.0)


def _extract_og_image(soup: BeautifulSoup) -> str | None:
    """OG 이미지 또는 첫 번째 기사 이미지 URL을 추출합니다."""
    # 1순위: og:image
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        url = og["content"].strip()
        if url.startswith("http"):
            return url

    # 2순위: twitter:image
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        url = tw["content"].strip()
        if url.startswith("http"):
            return url

    return None


async def _fetch_page(
    client: httpx.AsyncClient, url: str, source: str
) -> tuple[str, str | None]:
    """소스별 상세 페이지에서 (본문, 이미지 URL)을 추출합니다."""
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=_BODY_TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return "", None

    soup = BeautifulSoup(resp.text, "lxml")
    image_url = _extract_og_image(soup)

    selectors: list[str] = []
    if source == "pann":
        selectors = ["div.se-main-container", "div.post_cont", "div#contentArea"]
    elif source == "ruliweb":
        selectors = ["div.view_content", "div.board_content"]
    elif source == "naver_news":
        selectors = [
            # 네이버 뉴스 최신 (n.news.naver.com)
            "div#dic_area",
            "div.newsct_article",
            "article#dic_area",
            # 네이버 뉴스 구형
            "div._article_body_contents",
            "div#articleBodyContents",
            # 외부 언론사 공통 패턴
            "div.article_body",
            "div.article-body",
            "div.article-content",
            "div#article-view-content-div",
            "div.news_body",
            "div#newsct_article",
            "div.story-news",
            "div#articeBody",
            "div#articleBody",
            "div.article_txt",
            "section.article-body",
        ]

    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 50:
                return text[:3000], image_url

    # 마지막 fallback: <article> 태그
    el = soup.find("article")
    if el:
        text = el.get_text(separator="\n", strip=True)
        if len(text) > 50:
            return text[:3000], image_url

    return "", image_url


# 하위호환 래퍼 (news_crawler.py에서 사용)
async def _fetch_body(client: httpx.AsyncClient, url: str, source: str) -> str:
    body, _ = await _fetch_page(client, url, source)
    return body


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
    fetch_url: str = ""  # 본문 fetch용 URL (기본값: url과 동일)


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

    # 카테고리별 필수 키워드 (최소 1개 이상 매칭 필요)
    # society는 키워드 없이 와도 허용 (일반 사회 기사)
    _STRICT_CATEGORIES: set[str] = {"economy", "sports", "love"}

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

            # 여러 셀렉터 시도 (naver HTML 구조 변경 대응)
            candidates = soup.select(
                "div.rankingnews_box a.list_title, "
                "ul.rankingnews_list a, "
                "div.ranking_list a.nclicks, "
                "ol.list_ranking a.article"
            )

            for a in candidates:
                href = a.get("href", "")
                title = a.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                if "news.naver.com" not in href and not href.startswith("/"):
                    continue

                match = re.search(r"article/(\d+/\d+)", href)
                ext_id = match.group(1).replace("/", "_") if match else re.sub(r"[^\w]", "", href)[-30:]
                if ext_id in seen:
                    continue
                seen.add(ext_id)

                if not href.startswith("http"):
                    href = "https://news.naver.com" + href

                # 키워드 기반으로 실제 카테고리 검증
                # economy/sports/love는 키워드가 반드시 일치해야 함
                # society는 키워드 불일치해도 포함 (가장 일반적인 카테고리)
                guessed = _guess_category_from_title(title)
                if guessed == category:
                    assigned = category  # type: ignore[assignment]
                elif guessed != "story":
                    assigned = guessed  # 다른 카테고리 키워드 매칭 → 재분류
                elif category == "society":
                    assigned = "society"  # society 페이지 기사는 키워드 없어도 허용
                else:
                    # economy/sports/love 페이지인데 키워드 없음 → society로 fallback
                    assigned = "society"  # type: ignore[assignment]

                posts.append(CrawledPost(
                    source="naver_news",
                    external_id=ext_id,
                    title=title,
                    body="",
                    url=href,
                    category=assigned,
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

        # 상위 10개씩만 본문 fetch (동시 5개 제한)
        sem = asyncio.Semaphore(5)

        async def fill_body(post: CrawledPost) -> None:
            if post.body and post.image_url:
                return
            async with sem:
                target_url = post.fetch_url or post.url
                body, image_url = await _fetch_page(client, target_url, post.source)
                if body:
                    post.body = body
                if image_url and not post.image_url:
                    post.image_url = image_url

        await asyncio.gather(*[fill_body(p) for p in posts], return_exceptions=True)

    return posts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ECONOMY_KEYWORDS = re.compile(
    r"주식|코스피|코스닥|나스닥|비트코인|이더리움|환율|금리|부동산|아파트|ETF|펀드|채권|달러|원화|"
    r"경제|물가|증시|코인|투자|적금|통장|배당|증권|반도체|수출|수입|무역|관세|기업|삼성전자|SK하이닉스|"
    r"현대차|LG|취업|고용|실업|임금|연봉|월급|세금|기준금리|한국은행|Fed|연준|인플레|스태그플레이션", re.IGNORECASE
)
_SOCIETY_KEYWORDS = re.compile(
    r"정치|대통령|국회|선거|사건|사고|범죄|경찰|법원|외교|전쟁|군사|정부|판결|시위|파업|"
    r"검찰|수사|기소|구속|체포|살인|폭행|성범죄|마약|재판|헌법|헌재|탄핵|위헌|집회|"
    r"이민|이주|난민|인권|복지|의료|보건|코로나|감염|질병|사망|화재|사망|홍수|지진|재해", re.IGNORECASE
)
_SPORTS_KEYWORDS = re.compile(
    r"손흥민|이강인|류현진|박지성|김민재|황희찬|이정후|오타니|야구|축구|농구|배구|골프|올림픽|"
    r"월드컵|KBO|EPL|NBA|NFL|MLB|스포츠|득점|우승|MVP|리그|챔피언|토트넘|맨유|PSG|레알|바르셀로나|"
    r"대한민국 대표|국가대표|감독|코치|선발|홈런|골|경기|시즌|플레이오프", re.IGNORECASE
)
_LOVE_KEYWORDS = re.compile(
    r"연예인|아이돌|배우|가수|드라마|영화|열애|결별|폭로|스캔들|엔터테인먼트|데뷔|팬미팅|콘서트|"
    r"시상식|뮤직비디오|OST|컴백|활동중단|은퇴|소속사|BTS|방탄|블랙핑크|뉴진스|아이브|르세라핌|"
    r"에스파|NCT|엑소|트와이스|SM|YG|JYP|하이브|연기|수상|촬영|팬덤|팬|K팝|K-pop", re.IGNORECASE
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
