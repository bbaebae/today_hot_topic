"""커뮤니티/뉴스 크롤러.

소스:
  - 썰(story):   네이트판 베스트, 더쿠, 인스티즈, 오늘의유머, 개드립, 보배드림, MLB파크, 디시인사이드
  - 사회(society): 네이버 뉴스 사회 랭킹
  - 경제(economy): 네이버 뉴스 경제 랭킹
  - 스포츠(sports): 네이버 뉴스 스포츠 랭킹
  - 연애(love):   네이버 뉴스 연예 랭킹

각 커뮤니티 크롤러는 해당 시간대의 조회수 상위 5개 게시물을 반환합니다.
"""
from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}
_TIMEOUT = httpx.Timeout(15.0)
_BODY_TIMEOUT = httpx.Timeout(10.0)


def _normalize_url(url: str) -> str | None:
    """프로토콜 상대 URL(//)을 https://로, http://를 https://로 통일합니다.

    중복 제거 및 Mixed Content 경고 방지를 위해 모든 이미지 URL을 HTTPS로 저장.
    """
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://"):
        return "https://" + url[7:]
    if url.startswith("https://"):
        return url
    return None


def _unwrap_thumb(url: str) -> str:
    """thumb.pann.com/tc_WxH/ORIGINAL_URL 형태에서 원본 URL을 추출합니다."""
    m = re.match(r'https?://thumb\.pann\.com/tc_[^/]+/(https?://.+)', url)
    if m:
        return m.group(1)
    # http:// 원본 URL (프로토콜 누락)
    m = re.match(r'https?://thumb\.pann\.com/tc_[^/]+/(http://.+)', url)
    if m:
        return m.group(1)
    return url


_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".avif", ".svg"}


def _base_url(url: str) -> str:
    """중복 검사용 기본 URL.

    .jpg/.png 등 정적 이미지 확장자면 쿼리스트링 제거.
    download.jsp?FileID=xxx 같은 핸들러 URL은 쿼리스트링이 실제 식별자이므로
    전체 URL(쿼리스트링 포함)을 반환.
    """
    clean = url.split("|")[0]
    path = clean.split("?")[0]
    last_segment = path.rstrip("/").rsplit("/", 1)[-1]
    _, ext = os.path.splitext(last_segment)
    if ext.lower() in _IMAGE_EXTS:
        return path  # 정적 이미지: 쿼리스트링 제거
    return clean     # 핸들러 URL: 쿼리스트링 포함


def _extract_og_image(soup: BeautifulSoup) -> str | None:
    """OG 이미지 또는 첫 번째 기사 이미지 URL을 추출합니다."""
    # 1순위: og:image
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        url = _normalize_url(og["content"])
        if url:
            return _unwrap_thumb(url)

    # 2순위: twitter:image
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        url = _normalize_url(tw["content"])
        if url:
            return _unwrap_thumb(url)

    return None


_NEWS_JUNK_PATTERNS = [
    re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'),  # 이메일
    re.compile(r'등록\s*\d{4}[\.\-]\d{2}[\.\-]\d{2}'),                  # 등록 날짜
    re.compile(r'수정\s*\d{4}[\.\-]\d{2}[\.\-]\d{2}'),                  # 수정 날짜
    re.compile(r'^\s*\d{4}[\.\-]\d{2}[\.\-]\d{2}\s+\d{2}:\d{2}'),      # 날짜만 있는 줄
    re.compile(r'\[[^\]]*=[^\]]*\]\s*\S+\s*(기자|특파원|앵커)'),         # [지역=언론사]기자
    re.compile(r'^\s*(기자|특파원|앵커|편집자)\s*[=:]'),                  # 기자= 바이라인
    re.compile(r'(무단\s*전재|무단\s*복제|무단\s*배포|재배포\s*금지)'),   # 저작권
    re.compile(r'Copyright\s*(©|ⓒ|c)'),                                  # Copyright
    re.compile(r'^\s*(작게|크게|글자\s*크기)\s*$'),                       # 폰트 버튼
    re.compile(r'^\s*(공유|인쇄|스크랩|이메일|카카오|페이스북|트위터)\s*$'),  # 공유 버튼
]


def _clean_news_body(text: str) -> str:
    """뉴스 본문에서 기자 이메일·날짜·바이라인·저작권 등 불필요한 메타데이터를 제거합니다."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if any(pat.search(stripped) for pat in _NEWS_JUNK_PATTERNS):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()


def _is_content_image(url: str) -> bool:
    """콘텐츠 이미지인지 판별합니다 (아이콘/로고/광고 제외)."""
    low = url.lower()
    exclude = ("logo", "icon", "banner", "ad_", "/ads/", "advertisement",
               "spinner", "loading", "pixel", "tracking", "beacon",
               "1x1", "spacer", "blank")
    return not any(p in low for p in exclude)


def _add_image(url: str, found: list[str]) -> None:
    """중복 없이 이미지를 found 리스트에 추가합니다 (쿼리스트링 기준 중복 제거)."""
    url = _unwrap_thumb(url)
    base = _base_url(url)
    if not _is_content_image(url):
        return
    if any(_base_url(f) == base for f in found):
        return
    found.append(url)


def _collect_images(el: object, found: list[str], max_count: int = 10) -> None:
    """HTML 요소에서 이미지 URL을 추출하여 found 리스트에 추가합니다."""
    for img in el.find_all("img"):  # type: ignore[union-attr]
        if len(found) >= max_count:
            break
        # data-* 속성을 src보다 먼저 확인.
        # 판 등 lazy-loading 사이트는 src에 첫 번째 이미지(placeholder)를 반복 설정하고
        # 실제 각 이미지 URL은 data-original / data-src 등에 저장하기 때문.
        src = (
            img.get("data-original", "")
            or img.get("data-src", "")
            or img.get("data-lazy-src", "")
            or img.get("data-lazy", "")
            or img.get("data-url", "")
            or img.get("src", "")
        )
        norm = _normalize_url(src) if src else None
        if norm:
            _add_image(norm, found)


def _extract_rich_text(el: Tag) -> tuple[str, list[str]]:
    """DOM 요소를 순회하여 텍스트와 [IMG:url] 마커가 원본 위치에 삽입된 문자열을 반환합니다."""
    parts: list[str] = []
    images: list[str] = []
    seen_bases: set[str] = set()
    BLOCK_TAGS = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "li", "tr", "figure", "blockquote", "section"}

    def _get_img_src(img_tag: Tag) -> str | None:
        src = (
            img_tag.get("data-original", "")
            or img_tag.get("data-src", "")
            or img_tag.get("data-lazy-src", "")
            or img_tag.get("data-lazy", "")
            or img_tag.get("data-url", "")
            or img_tag.get("src", "")
        )
        norm = _normalize_url(src) if src else None
        # pann thumb URL 언래핑: thumb.pann.com/tc_WxH/ORIGINAL_URL → ORIGINAL_URL
        return _unwrap_thumb(norm) if norm else None

    def walk(node: NavigableString | Tag) -> None:
        if isinstance(node, NavigableString):
            t = str(node)
            if t.strip():
                parts.append(t)
            return
        if not isinstance(node, Tag):
            return
        if node.name in ("script", "style", "noscript"):
            return
        if node.name == "img":
            if len(images) >= 10:
                return
            norm = _get_img_src(node)
            if norm and _is_content_image(norm):
                base = _base_url(norm)
                if base not in seen_bases:
                    seen_bases.add(base)
                    parts.append(f"\n[IMG:{norm}]\n")
                    images.append(norm)
            return
        is_block = node.name in BLOCK_TAGS
        if is_block:
            parts.append("\n")
        for child in node.children:
            walk(child)
        if is_block:
            parts.append("\n")

    for child in el.children:
        walk(child)

    text = "".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), images


async def _fetch_page(
    client: httpx.AsyncClient, url: str, source: str
) -> tuple[str, list[str], list[str]]:
    """소스별 상세 페이지에서 (본문+인라인이미지마커, 이미지 URL 리스트, 베스트댓글 리스트)를 추출합니다.
    본문에는 이미지 원본 위치에 [IMG:url] 마커가 삽입됩니다.
    """
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=_BODY_TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return "", [], []

    soup = BeautifulSoup(resp.text, "lxml")
    og_image = _extract_og_image(soup)

    _is_news = source in ("naver_news", "rss_news")

    def _finalize(el: Tag, is_news: bool, og: str | None, comments: list[str]) -> tuple[str, list[str], list[str]]:
        """junk 제거 후 rich text 추출 + og_image fallback 처리."""
        text, images = _extract_rich_text(el)
        if is_news:
            text = _clean_news_body(text)
        # 뉴스: 인라인 이미지가 없으면 og_image를 imageUrls에만 추가 (body에는 삽입 안 함)
        # → 프론트에서 레거시 상단 배치로 자동 처리됨
        if is_news and not images and og and _is_content_image(og):
            images = [og]
        # 커뮤니티(story): 인라인 이미지 없으면 og_image를 body 맨 앞에 마커로 삽입
        if not is_news and not images and og and _is_content_image(og):
            text = f"[IMG:{og}]\n\n{text}" if text else f"[IMG:{og}]"
            images = [og]
        return text[:6000], images[:10], comments

    selectors: list[str] = []
    if source == "pann":
        selectors = [
            "div#contentArea",
            "div.se-main-container",
            "div.post_cont",
            "div.view_content",
            "div.talk_cont",
        ]
    elif source == "theqoo":
        selectors = ["div.xe_content", "div.read_body", "div.document_content"]
    elif source == "instiz":
        selectors = ["div.memo_content", "div#memo_content_s", "div.view_content"]
    elif source == "todayhumor":
        selectors = ["div.viewContent", "div#viewer", "div.view_body"]
    elif source == "gaeddip":
        selectors = ["div.view-content", "div#post-content", "div.article-body"]
    elif source == "bobaedream":
        selectors = [
            "div.bodyCont",
            "div.bobaContents",
            "div.boba-content",
            "div.view_cont",
            "div#content_area",
            "div.post_content",
        ]
    elif source == "mlbpark":
        selectors = ["div.viewContent", "div#viewContent", "div.view_body"]
    elif source == "dcinside":
        selectors = [
            "div.write_div",
            "div.gallview_contents",
            "div#container div.write_div",
            "div.inner.clear",
        ]
    elif _is_news:
        # 세계일보: div#mcontent는 사이드바·광고 포함 → article.viewBox2만 사용
        if "segye.com" in url:
            el = soup.select_one("article.viewBox2") or soup.select_one("div#article_txt")
            if el:
                for junk in el.select(
                    "div.newsct_journalist, div.media_journalistcard_item, "
                    "div.media_end_head_journalist_thumb, "
                    "div.viewInfo, div.viewHelp, "
                    "aside, .relate_news, .related"
                ):
                    junk.decompose()
                for img in el.find_all("img"):
                    src = img.get("src", "") or ""
                    if "img_people" in src or "ico_" in src:
                        img.decompose()
                return _finalize(el, True, og_image, [])

        # 뉴시스
        if "newsis.com" in url:
            el = soup.select_one("div.articleView div.view") or soup.select_one("div#articleView")
            if el:
                for junk in el.select("div.infoLine, div.link_list, div.reporter_area, div.keywords, aside, .relate_news"):
                    junk.decompose()
                return _finalize(el, True, og_image, [])

        # 조선일보
        if "chosun.com" in url:
            el = soup.select_one("section.article-body") or soup.select_one("section[itemprop='articleBody']")
            if el:
                for junk in el.select("div.arcad-wrapper, div.dfpAd, aside, .relate_news"):
                    junk.decompose()
                return _finalize(el, True, og_image, [])

        selectors = [
            "div#dic_area",
            "div.newsct_article",
            "article#dic_area",
            "div._article_body_contents",
            "div#articleBodyContents",
            "div.articleView div.view",
            "div.main_view",
            "div.art_body",
            "div#articleBody",
            "div#content",
            "div.view_article",
            "div.article_view",
            "div.article_body",
            "div.article-body",
            "div.article-content",
            "div#article-view-content-div",
            "div.news_body",
            "div#newsct_article",
            "div.story-news",
            "div#articeBody",
            "div.article_txt",
            "section.article-body",
            "div#articleText",
            "div#news_body_area",
            "div.view-content",
        ]

    comments = [] if _is_news else await _fetch_comments(soup, source, client=client, url=url)

    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text, images = _extract_rich_text(el)
            if len(text.replace("\n", "").strip()) > 50 or images:
                if _is_news:
                    text = _clean_news_body(text)
                    # 뉴스: og_image를 imageUrls에만 (body에 삽입 안 함)
                    if not images and og_image and _is_content_image(og_image):
                        images = [og_image]
                else:
                    # 커뮤니티: og_image를 body 마커로 삽입
                    if not images and og_image and _is_content_image(og_image):
                        text = f"[IMG:{og_image}]\n\n{text}" if text else f"[IMG:{og_image}]"
                        images = [og_image]
                return text[:6000], images[:10], comments

    # 마지막 fallback: <article> 태그
    el = soup.find("article")
    if el:
        text, images = _extract_rich_text(el)
        if len(text.replace("\n", "").strip()) > 50 or images:
            if _is_news:
                text = _clean_news_body(text)
                if not images and og_image and _is_content_image(og_image):
                    images = [og_image]
            else:
                if not images and og_image and _is_content_image(og_image):
                    text = f"[IMG:{og_image}]\n\n{text}" if text else f"[IMG:{og_image}]"
                    images = [og_image]
            return text[:6000], images[:10], comments

    # og_image만 있는 경우 (커뮤니티: 마커 삽입, 뉴스: imageUrls에만)
    if og_image and _is_content_image(og_image):
        if _is_news:
            return "", [og_image], comments
        return f"[IMG:{og_image}]", [og_image], comments
    return "", [], comments


# 하위호환 래퍼 (news_crawler.py에서 사용)
async def _fetch_body(client: httpx.AsyncClient, url: str, source: str) -> str:
    body, _, _ = await _fetch_page(client, url, source)
    return body


async def _fetch_comments(
    soup: BeautifulSoup, source: str,
    client: httpx.AsyncClient | None = None, url: str = ""
) -> list[str]:
    """커뮤니티 게시글의 베스트 댓글을 추출합니다. 실패 시 빈 리스트 반환."""
    candidates: list[str] = []

    if source == "pann":
        # 네이트판: 댓글이 AJAX로 로드됨 → /talk/reply/loadBeple API 직접 호출
        pann_id_match = re.search(r"/talk/(\d+)", url)
        if pann_id_match and client:
            pann_id = pann_id_match.group(1)
            try:
                resp = await client.post(
                    "https://pann.nate.com/talk/reply/loadBeple",
                    data={"pann_id": pann_id, "reply_page": "1"},
                    headers={**_HEADERS, "X-Requested-With": "XMLHttpRequest",
                              "Referer": url},
                    timeout=10,
                )
                bepl_soup = BeautifulSoup(resp.text, "lxml")
                for el in bepl_soup.select("dd.usertxt"):
                    t = el.get_text(strip=True)
                    if t:
                        candidates.append(t)
            except Exception:
                pass

    elif source == "theqoo":
        for el in soup.select(".comment_body .xe_content, .fb-comment-item .comment_content"):
            t = el.get_text(strip=True)
            if t:
                candidates.append(t)

    elif source == "instiz":
        for el in soup.select(".comment_content, .comment_text_wrap p"):
            t = el.get_text(strip=True)
            if t:
                candidates.append(t)

    elif source == "todayhumor":
        for el in soup.select("table.view_reply .view_reple_text, .replyContent"):
            t = el.get_text(strip=True)
            if t:
                candidates.append(t)

    elif source == "gaeddip":
        for el in soup.select(".comment-body p, .comment-text, .comment-content"):
            t = el.get_text(strip=True)
            if t:
                candidates.append(t)

    elif source == "bobaedream":
        # 보배드림: 베스트댓글은 id="bepl_small_cmt_*" 형태로 메인 HTML에 존재
        for el in soup.select("[id^='bepl_small_cmt_']"):
            t = el.get_text(strip=True)
            if t:
                candidates.append(t)

    elif source == "mlbpark":
        for el in soup.select(".reComment_body .txt, .cmt_txt"):
            t = el.get_text(strip=True)
            if t:
                candidates.append(t)

    elif source == "dcinside":
        for el in soup.select(".cmt_list .ub-content .usertxt, span.usertxt.ub-word"):
            t = el.get_text(strip=True)
            if t:
                candidates.append(t)

    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        c = c[:120]
        if c not in seen and len(c) >= 5:
            seen.add(c)
            result.append(c)
        if len(result) >= 10:
            break
    return result


@dataclass
class CrawledPost:
    source: str
    external_id: str
    title: str
    body: str
    url: str
    category: Category
    image_url: str | None = None
    image_urls: list[str] = field(default_factory=list)
    view_count: int = 0
    fetch_url: str = ""  # 본문 fetch용 URL (기본값: url과 동일)
    top_comments: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 네이트판 베스트 (썰)
# ---------------------------------------------------------------------------

class PannCrawler:
    # 실시간 인기톡 AJAX 엔드포인트 (classId=0: 전체)
    _URL = "https://pann.nate.com/talk/category/ClassList?classId=0&page=1"
    _BASE = "https://pann.nate.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            headers = {
                **_HEADERS,
                "Referer": "https://pann.nate.com/talk",
                "X-Requested-With": "XMLHttpRequest",
            }
            resp = await client.get(self._URL, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        for li in soup.select("ul.post_wrap li"):
            # 제목 링크
            dt_a = li.select_one("dt a[href*='/talk/']")
            if not dt_a:
                continue

            href = dt_a.get("href", "")
            if not href.startswith("http"):
                href = self._BASE + href

            match = re.search(r"/talk/(\d+)", href)
            if not match:
                continue
            ext_id = match.group(1)
            if ext_id in seen:
                continue
            seen.add(ext_id)

            title = dt_a.get("title", "") or dt_a.get_text(strip=True)
            if not title or len(title) < 2:
                continue

            # 본문 미리보기 (dd.txt)
            txt_el = li.select_one("dd.txt a")
            body = txt_el.get_text(strip=True) if txt_el else ""

            # 썸네일 이미지 (있는 글만)
            img_el = li.select_one("div.thumb img")
            image_url = img_el.get("src") if img_el else None

            # 댓글 수를 인기도 대리 지표로 사용
            reple_el = li.select_one("span.reple-num")
            reple_text = reple_el.get_text(strip=True).strip("()") if reple_el else "0"
            comment_count = _parse_count(reple_text)

            posts.append(CrawledPost(
                source="pann",
                external_id=ext_id,
                title=title,
                body=body,
                url=href,
                category="story",
                image_url=image_url,
                view_count=comment_count,  # 댓글 수 기준 정렬
            ))

        posts.sort(key=lambda p: p.view_count, reverse=True)
        return posts[:10]


# ---------------------------------------------------------------------------
# 더쿠 핫게시판 (썰)
# ---------------------------------------------------------------------------

class TheqooCrawler:
    _URL = "https://theqoo.net/hot"
    _BASE = "https://theqoo.net"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            headers = {**_HEADERS, "Referer": "https://theqoo.net/"}
            resp = await client.get(self._URL, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        # 더쿠는 XE 기반 게시판을 사용
        rows = (
            soup.select("table.tbl_board tbody tr")
            or soup.select("ul.list_articles li")
            or soup.select("div.boardContents li")
        )

        for row in rows:
            # 제목 링크
            a = (
                row.select_one("td.title a, td.subject a, a.title")
                or row.select_one("a[href*='/hot/']")
                or row.select_one("span.title a, a")
            )
            if not a:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = a.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = self._BASE + href

            # ext_id 추출
            match = re.search(r"/(\d+)(?:\?|$|#)", href) or re.search(r"no=(\d+)", href)
            if not match:
                continue
            ext_id = f"theqoo_{match.group(1)}"
            if ext_id in seen:
                continue
            seen.add(ext_id)

            # 조회수
            view_el = (
                row.select_one("td.view_cnt, td.hits, td.count, span.cnt")
                or row.select_one("em.view, span.view, .view_count")
            )
            view_count = _parse_count(view_el.get_text(strip=True)) if view_el else 0

            posts.append(CrawledPost(
                source="theqoo",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
                view_count=view_count,
            ))

        posts.sort(key=lambda p: p.view_count, reverse=True)
        return posts[:5]


# ---------------------------------------------------------------------------
# 인스티즈 (썰)
# ---------------------------------------------------------------------------

class InstizCrawler:
    _URL = "https://www.instiz.net/pt"
    _BASE = "https://www.instiz.net"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            resp = await client.get(self._URL, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        # 인스티즈 게시판 구조
        rows = (
            soup.select("table.board_list tr[class*='list']")
            or soup.select("ul.board_list li")
            or soup.select("table tbody tr")
        )

        for row in rows:
            a = (
                row.select_one("td.listsubject a, td.subject a")
                or row.select_one("a[href*='no=']")
                or row.select_one("span.subject a, a.subject")
            )
            if not a:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = a.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = self._BASE + href

            match = re.search(r"no=(\d+)", href) or re.search(r"/pt/(\d+)", href)
            if not match:
                continue
            ext_id = f"instiz_{match.group(1)}"
            if ext_id in seen:
                continue
            seen.add(ext_id)

            # 조회수
            view_el = row.select_one("td.view, td.listview, td.hit, span.view")
            view_count = _parse_count(view_el.get_text(strip=True)) if view_el else 0

            posts.append(CrawledPost(
                source="instiz",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
                view_count=view_count,
            ))

        posts.sort(key=lambda p: p.view_count, reverse=True)
        return posts[:5]


# ---------------------------------------------------------------------------
# 오늘의유머 베스트오브베스트 (썰)
# ---------------------------------------------------------------------------

class TodayHumorCrawler:
    _URL = "https://www.todayhumor.co.kr/board/list.php?table=bestofbest"
    _BASE = "https://www.todayhumor.co.kr"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            resp = await client.get(self._URL, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        rows = (
            soup.select("table.table_list tr.view")
            or soup.select("table.table_list tr")
            or soup.select("tbody tr")
        )

        for row in rows:
            a = (
                row.select_one("td.subject a, a.subject_link")
                or row.select_one("td.title a")
                or row.select_one("a[href*='view.php']")
            )
            if not a:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = a.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = self._BASE + "/" + href.lstrip("/")

            match = re.search(r"no=(\d+)", href)
            if not match:
                continue
            ext_id = f"todayhumor_{match.group(1)}"
            if ext_id in seen:
                continue
            seen.add(ext_id)

            # 조회수
            view_el = row.select_one("td.view, td.hits, td.count, td:nth-child(5)")
            view_count = _parse_count(view_el.get_text(strip=True)) if view_el else 0

            posts.append(CrawledPost(
                source="todayhumor",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
                view_count=view_count,
            ))

        posts.sort(key=lambda p: p.view_count, reverse=True)
        return posts[:5]


# ---------------------------------------------------------------------------
# 개드립 베스트 (썰)
# ---------------------------------------------------------------------------

class GaeddipCrawler:
    _URL = "https://www.gaeddip.com/bbs/board.php?bo_table=best"
    _BASE = "https://www.gaeddip.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            resp = await client.get(self._URL, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        rows = (
            soup.select("section.bo_list ul li, div.bo_list ul li")
            or soup.select("table.board_list tr")
            or soup.select("ul.board-list li")
            or soup.select("tbody tr")
        )

        for row in rows:
            a = (
                row.select_one("a.bo_tit, a.title, strong.bo_tit a")
                or row.select_one("td.td_subject a")
                or row.select_one("a[href*='wr_id=']")
            )
            if not a:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = a.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = self._BASE + href

            match = re.search(r"wr_id=(\d+)", href)
            if not match:
                continue
            ext_id = f"gaeddip_{match.group(1)}"
            if ext_id in seen:
                continue
            seen.add(ext_id)

            # 조회수
            view_el = row.select_one("td.td_num2, span.view, .hit, td.hits")
            view_count = _parse_count(view_el.get_text(strip=True)) if view_el else 0

            posts.append(CrawledPost(
                source="gaeddip",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
                view_count=view_count,
            ))

        posts.sort(key=lambda p: p.view_count, reverse=True)
        return posts[:10]


# ---------------------------------------------------------------------------
# 보배드림 자유게시판 (썰)
# ---------------------------------------------------------------------------

class BobaedreamCrawler:
    # 주간 베스트 게시판
    _URL = "https://www.bobaedream.co.kr/board/bulletin/list.php?code=best&vdate=w"
    _BASE = "https://www.bobaedream.co.kr"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            resp = await client.get(self._URL, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        # a.bsubject: 실제 게시글 제목 링크 (댓글 링크 제외)
        anchors = soup.select("a.bsubject[href*='No=']")

        for a in anchors:
            title = a.get("title", "") or a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = a.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = self._BASE + href

            match = re.search(r"No=(\d+)", href)
            if not match:
                continue
            ext_id = f"bobaedream_{match.group(1)}"
            if ext_id in seen:
                continue
            seen.add(ext_id)

            posts.append(CrawledPost(
                source="bobaedream",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                fetch_url=href,
                category="story",
                view_count=0,
            ))

        return posts[:10]


# ---------------------------------------------------------------------------
# MLB파크 자유게시판 (썰)
# ---------------------------------------------------------------------------

class MlbparkCrawler:
    _URL = "https://bbs.mlbpark.com/mlbpark/?m=bbs_list&bbs=mlbpark_free"
    _BASE = "https://bbs.mlbpark.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            resp = await client.get(self._URL, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        rows = (
            soup.select("table.bbs_list tr.bbs-list")
            or soup.select("table.list-table tbody tr")
            or soup.select("tbody tr")
        )

        for row in rows:
            a = (
                row.select_one("td.title a, td.subject a")
                or row.select_one("a[href*='bbs_view']")
                or row.select_one("a[href*='idx=']")
            )
            if not a:
                continue

            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = a.get("href", "")
            if not href:
                continue
            if not href.startswith("http"):
                href = self._BASE + href

            match = (
                re.search(r"idx=(\d+)", href)
                or re.search(r"id=(\d+)", href)
                or re.search(r"/(\d+)$", href)
            )
            if not match:
                continue
            ext_id = f"mlbpark_{match.group(1)}"
            if ext_id in seen:
                continue
            seen.add(ext_id)

            # 조회수
            view_el = row.select_one("td.view, td.count, td.hits, span.view")
            view_count = _parse_count(view_el.get_text(strip=True)) if view_el else 0

            posts.append(CrawledPost(
                source="mlbpark",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
                view_count=view_count,
            ))

        posts.sort(key=lambda p: p.view_count, reverse=True)
        return posts[:5]


# ---------------------------------------------------------------------------
# 디시인사이드 이슈 갤러리 (썰)
# ---------------------------------------------------------------------------

class DcinsideCrawler:
    # DC 베스트 갤러리 - 실시간 인기 게시물
    _URL = "https://gall.dcinside.com/board/lists/?id=dcbest"
    _BASE = "https://gall.dcinside.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[CrawledPost]:
        try:
            headers = {**_HEADERS, "Referer": "https://www.dcinside.com/"}
            resp = await client.get(self._URL, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        posts: list[CrawledPost] = []
        seen: set[str] = set()

        # data-no 속성이 있는 실제 게시글 행만 선택 (공지·설문 제외)
        rows = (
            soup.select("tr.us-post[data-no]")
            or soup.select("tr[data-no]:not([data-type='icon_notice'])")
            or soup.select("table.gall_list tbody tr[data-no]")
        )

        for row in rows:
            data_no = row.get("data-no", "")
            if not data_no:
                continue

            a = row.select_one("td.gall_tit a, td.subject a")
            if not a:
                continue

            # 제목: <strong>[갤명]</strong> 텍스트 제거 후 추출
            strong = a.find("strong")
            if strong:
                strong.decompose()
            title = a.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            href = a.get("href", "")
            if href and not href.startswith("http"):
                href = self._BASE + href
            if not href:
                href = f"{self._BASE}/board/view/?id=dcbest&no={data_no}"

            ext_id = f"dcinside_{data_no}"
            if ext_id in seen:
                continue
            seen.add(ext_id)

            # 썸네일 이미지 (.thumimg img)
            img_el = row.select_one(".thumimg img")
            image_url: str | None = None
            if img_el:
                src = img_el.get("src", "")
                if src and src.startswith("http"):
                    image_url = src

            # 조회수
            view_el = row.select_one("td.gall_count, td.count, span.view_cnt")
            view_count = _parse_count(view_el.get_text(strip=True)) if view_el else 0

            posts.append(CrawledPost(
                source="dcinside",
                external_id=ext_id,
                title=title,
                body="",
                url=href,
                category="story",
                view_count=view_count,
                image_url=image_url,
            ))

        posts.sort(key=lambda p: p.view_count, reverse=True)
        return posts[:10]


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

# ---------------------------------------------------------------------------
# 전체 크롤링 실행 (커뮤니티 썰만 — 뉴스는 news_crawler.py에서 RSS로 처리)
# ---------------------------------------------------------------------------

async def crawl_all() -> list[CrawledPost]:
    """커뮤니티 크롤러를 병렬 실행하고 결과를 반환합니다.

    각 커뮤니티 크롤러는 해당 시간대 조회수 기준 상위 5개를 반환합니다.
    전체 랭킹은 recompute_ranks()에서 조회수 × 최신성 점수로 계산됩니다.
    뉴스(사회/경제/스포츠/연예)는 news_crawler.crawl_news()가 담당합니다.
    """
    crawlers = [
        PannCrawler(),
        BobaedreamCrawler(),
        DcinsideCrawler(),
    ]
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
            if post.body and post.image_urls:
                return
            async with sem:
                target_url = post.fetch_url or post.url
                body, fetched_images, comments = await _fetch_page(client, target_url, post.source)
                if body:
                    post.body = body
                if comments:
                    post.top_comments = comments
                # 목록 썸네일 → 원본 URL 변환 + https 통일
                if post.image_url:
                    post.image_url = _normalize_url(_unwrap_thumb(post.image_url))
                # 대표 이미지: pann은 목록 페이지 썸네일 우선
                if fetched_images and not post.image_url and post.source != "pann":
                    post.image_url = fetched_images[0]
                # 전체 이미지 목록 구성 (대표 이미지 먼저, 중복 제거)
                all_imgs: list[str] = []
                if post.image_url:
                    _add_image(post.image_url, all_imgs)  # 동일 기준으로 중복 제거
                for img in fetched_images:
                    _add_image(img, all_imgs)
                post.image_urls = all_imgs[:10]
                # 아이콘/로고 등 비콘텐츠 이미지가 image_url에 남아있으면 정리
                if post.image_url and not _is_content_image(post.image_url):
                    post.image_url = all_imgs[0] if all_imgs else None

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
            return min(int(float(text.replace("만", "")) * 10000), 100_000_000)
        except ValueError:
            return 0
    try:
        val = int(re.sub(r"[^\d]", "", text) or "0")
        return min(val, 100_000_000)
    except ValueError:
        return 0
