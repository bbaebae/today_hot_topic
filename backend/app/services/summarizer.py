"""OpenAI GPT-4o 기반 커뮤니티 게시물 3줄 요약."""
from __future__ import annotations

import json

from openai import AsyncOpenAI

from ..config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)

_SYSTEM_PROMPT = """\
당신은 커뮤니티 핫이슈를 분석하는 전문가입니다.
다음 규칙을 반드시 지켜주세요:
1. 핵심 내용을 담은 문장 3개를 작성합니다 (각 40자 이내, 경어체 ~해요/~예요).
2. 이 이슈의 핵심 쟁점에 맞는 찬반 투표 선택지 2개를 작성합니다 (각 15자 이내).
   - 선택지는 단순히 "찬성/반대"가 아니라 이슈의 맥락에 맞는 구체적인 표현이어야 합니다.
   - 예: 연봉 협상 이슈라면 "더 요구해야 해" / "지금도 충분해"
   - 예: 연예인 열애 이슈라면 "잘 어울려요" / "의외의 조합이에요"
3. 특수문자나 마크다운은 사용하지 않습니다.
4. 반드시 {"summary": ["문장1", "문장2", "문장3"], "poll": ["선택지A", "선택지B"]} 형식의 JSON으로만 답변합니다.
본문이 없으면 제목만으로 추측해서 작성합니다.
"""

_DEFAULT_POLL_FALLBACK: dict[str, tuple[str, str]] = {
    "story":   ("공감해요", "공감 안 해요"),
    "society": ("사실이에요", "과장된 것 같아요"),
    "economy": ("오를 것 같아요", "내릴 것 같아요"),
    "sports":  ("잘할 것 같아요", "못할 것 같아요"),
    "love":    ("이해해요", "이해 못 하겠어요"),
}


async def summarize(
    title: str,
    body: str,
    category: str = "story",
    image_urls: list[str] | None = None,
) -> tuple[list[str], tuple[str, str]]:
    """
    게시물 제목과 본문을 받아 (3줄 요약, 투표 선택지 2개) 튜플을 반환합니다.
    본문이 없고 이미지가 있으면 GPT-4o vision으로 이미지를 분석합니다.
    실패 시 fallback을 반환합니다.
    """
    use_vision = not body.strip() and bool(image_urls)

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
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0.4,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
        else:
            content_part = f"\n\n본문:\n{body[:3000]}" if body.strip() else ""
            prompt = f"제목: {title}{content_part}"
            resp = await _client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
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
            summary = _fallback_summary(title)

        # poll 파싱
        poll_raw = parsed.get("poll", [])
        if isinstance(poll_raw, list) and len(poll_raw) >= 2 and all(isinstance(x, str) for x in poll_raw[:2]):
            poll = (poll_raw[0][:20], poll_raw[1][:20])
        else:
            poll = _DEFAULT_POLL_FALLBACK.get(category, ("찬성해요", "반대해요"))

        return summary, poll

    except Exception:
        return _fallback_summary(title), _DEFAULT_POLL_FALLBACK.get(category, ("찬성해요", "반대해요"))


def _fallback_summary(title: str) -> list[str]:
    return [
        f"'{title}' 이슈가 커뮤니티에서 주목받고 있어요.",
        "네티즌들 사이에서 다양한 의견이 오가고 있어요.",
        "자세한 내용은 원문 링크를 확인해 보세요.",
    ]
