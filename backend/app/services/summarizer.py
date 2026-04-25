"""OpenAI GPT-4o 기반 커뮤니티/뉴스 3줄 요약."""
from __future__ import annotations

import json

from openai import AsyncOpenAI

from ..config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)

_SYSTEM_PROMPT_COMMUNITY = """\
당신은 커뮤니티 핫이슈를 분석하는 전문가입니다.
다음 규칙을 반드시 지켜주세요:
1. 핵심 내용을 담은 문장 3개를 작성합니다 (각 40자 이내, 경어체 ~해요/~예요).
2. 본문과 베스트 댓글을 읽고 사람들이 실제로 어떤 지점에서 의견이 갈리는지 파악하여, 읽는 순간 바로 누르고 싶어지는 투표 선택지 2개를 만듭니다 (각 15자 이내).
   - 선택지는 도파민이 터질 만큼 자극적이고 직접적이어야 합니다. 강한 구어체, 인터넷 말투 환영.
   - "찬성해요/반대해요", "맞아요/아니에요" 같은 밋밋한 표현은 절대 금지.
   - 베스트 댓글이 있으면 반드시 참고하여 실제 독자가 나뉘는 지점을 뾰족하게 표현하세요.
   - 예시 (참고만, 그대로 쓰지 말 것):
     * 직장 갑질: "당장 신고각이죠" / "참는 게 이득이에요"
     * 연봉 협상: "더 뜯어내야죠" / "그냥 받아요"
     * 연예인 열애: "완전 찰떡이에요" / "진짜 의외인데요"
     * 부모 갈등: "부모가 맞아요" / "자식이 맞아요"
     * 음식 논란: "나는 먹겠어요" / "절대 못 먹겠어요"
3. 특수문자나 마크다운은 사용하지 않습니다.
4. 반드시 {"summary": ["문장1", "문장2", "문장3"], "poll": ["선택지A", "선택지B"]} 형식의 JSON으로만 답변합니다.
본문이 없으면 제목만으로 추측해서 작성합니다.
"""

_SYSTEM_PROMPT_NEWS = """\
당신은 뉴스 기사를 분석하는 전문가입니다.
다음 규칙을 반드시 지켜주세요:
1. 기사의 핵심 내용을 담은 문장 3개를 작성합니다 (각 40자 이내, 경어체 ~해요/~예요).
2. 기사가 독자에게 던지는 핵심 질문을 찾아, 읽는 순간 바로 누르고 싶어지는 투표 선택지 2개를 만듭니다 (각 15자 이내).
   - 선택지는 도파민이 터질 만큼 자극적이고 직접적이어야 합니다. 강한 구어체 환영.
   - "찬성해요/반대해요" 같은 밋밋한 표현 절대 금지. 기사 내용에서 직접 뽑은 뾰족한 표현이어야 합니다.
   - 카테고리별 가이드 (기사 내용이 더 중요):
     * 주가/증시/코스피/코스닥/나스닥: "오른다에 베팅해요" / "내린다에 베팅해요"
     * 금리/통화정책: "불가피한 선택이에요" / "최악의 타이밍이에요"
     * 기업 실적/전망: "기대 이상일 거예요" / "실망스러울 거예요"
     * 사건/사고/정책: 해당 결정의 핵심을 직접 찌르는 강한 표현
     * 스포츠: "무조건 해낼 거예요" / "이번엔 힘들 것 같아요"
     * 연예: "완전 찰떡이에요" / "진짜 의외인데요"
3. 특수문자나 마크다운은 사용하지 않습니다.
4. 반드시 {"summary": ["문장1", "문장2", "문장3"], "poll": ["선택지A", "선택지B"]} 형식의 JSON으로만 답변합니다.
본문이 없으면 제목만으로 추측해서 작성합니다.
"""

_DEFAULT_POLL_FALLBACK: dict[str, tuple[str, str]] = {
    "story":   ("공감해요", "공감 안 해요"),
    "society": ("타당해요", "납득 안 돼요"),
    "economy": ("긍정적이에요", "부정적이에요"),
    "sports":  ("잘할 것 같아요", "힘들 것 같아요"),
    "love":    ("이해해요", "이해 못 하겠어요"),
}

# 주가/증시 관련 키워드 → 오를/내릴 폴 적용
_STOCK_KEYWORDS = (
    "주가", "주식", "코스피", "코스닥", "증시", "상장", "시총", "시가총액",
    "나스닥", "다우", "s&p", "sp500", "etf", "배당", "공모주", "ipo",
    "급등", "급락", "상승세", "하락세", "52주 신고", "52주 신저",
)


def _is_stock_article(title: str, body: str = "") -> bool:
    """주가/증시 관련 기사인지 제목+본문 키워드로 판별합니다."""
    text = (title + " " + body[:200]).lower()
    return any(kw in text for kw in _STOCK_KEYWORDS)


async def summarize(
    title: str,
    body: str,
    category: str = "story",
    image_urls: list[str] | None = None,
    top_comments: list[str] | None = None,
) -> tuple[list[str], tuple[str, str]]:
    """
    게시물 제목과 본문을 받아 (3줄 요약, 투표 선택지 2개) 튜플을 반환합니다.
    본문이 없고 이미지가 있으면 GPT-4o vision으로 이미지를 분석합니다.
    실패 시 fallback을 반환합니다.
    """
    is_news = category in ("society", "economy", "sports", "love")
    system_prompt = _SYSTEM_PROMPT_NEWS if is_news else _SYSTEM_PROMPT_COMMUNITY
    use_vision = not body.strip() and bool(image_urls)
    # 주가 관련 기사 여부 (fallback poll 결정용)
    is_stock = category == "economy" and _is_stock_article(title, body)

    try:
        if use_vision:
            # 이미지 분석 모드
            content: list[dict] = [
                {"type": "text", "text": f"제목: {title}\n\n이미지를 보고 내용을 파악해 주세요:"},
            ]
            for img_url in (image_urls or [])[:5]:
                content.append({"type": "image_url", "image_url": {"url": img_url}})
            resp = await _client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                temperature=0.4,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
        else:
            content_part = f"\n\n본문:\n{body[:3000]}" if body.strip() else ""
            comments_part = ""
            if top_comments:
                comments_list = "\n".join(f"- {c}" for c in top_comments[:5])
                comments_part = f"\n\n베스트 댓글:\n{comments_list}"
            prompt = f"제목: {title}{content_part}{comments_part}"
            resp = await _client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
        raw = resp.choices[0].message.content or "{}"
        parsed = json.loads(raw)

        # summary 파싱
        summary: list[str] = []
        for key in ("summary", "summaries", "lines", "result"):
            if key in parsed and isinstance(parsed[key], list):
                summary = [s for s in parsed[key][:3] if s]
                break
        if not summary:
            for v in parsed.values():
                if isinstance(v, list) and v:
                    summary = [s for s in v[:3] if s]
                    break
        if not summary:
            summary = _fallback_summary(title, is_news)

        # poll 파싱
        poll_raw = parsed.get("poll", [])
        if isinstance(poll_raw, list) and len(poll_raw) >= 2 and all(isinstance(x, str) for x in poll_raw[:2]):
            poll = (poll_raw[0][:20], poll_raw[1][:20])
        else:
            poll = _default_poll(category, is_stock)

        return summary, poll

    except Exception:
        return _fallback_summary(title, is_news), _default_poll(category, is_stock)


def _default_poll(category: str, is_stock: bool = False) -> tuple[str, str]:
    """카테고리와 주가 여부에 따라 기본 투표 선택지를 반환합니다."""
    if is_stock:
        return ("오를 것 같아요", "내릴 것 같아요")
    return _DEFAULT_POLL_FALLBACK.get(category, ("찬성해요", "반대해요"))


def _fallback_summary(title: str, is_news: bool = False) -> list[str]:
    if is_news:
        return [
            f"'{title}' 기사가 주목받고 있어요.",
            "다양한 시각에서 분석이 이루어지고 있어요.",
            "자세한 내용은 원문 링크를 확인해 보세요.",
        ]
    return [
        f"'{title}' 이슈가 커뮤니티에서 주목받고 있어요.",
        "네티즌들 사이에서 다양한 의견이 오가고 있어요.",
        "자세한 내용은 원문 링크를 확인해 보세요.",
    ]
