"""OpenAI GPT-4o 기반 커뮤니티 게시물 3줄 요약."""
from __future__ import annotations

import json

from openai import AsyncOpenAI

from ..config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)

_SYSTEM_PROMPT = """\
당신은 커뮤니티 핫이슈를 3줄로 요약하는 전문가입니다.
다음 규칙을 반드시 지켜주세요:
1. 핵심 내용을 담은 문장 3개만 작성합니다.
2. 각 문장은 40자 이내로 간결하게 작성합니다.
3. 경어체(~해요, ~예요)를 사용합니다.
4. 특수문자나 마크다운은 사용하지 않습니다.
5. 반드시 {"summary": ["문장1", "문장2", "문장3"]} 형식의 JSON으로만 답변합니다.
본문이 없으면 제목만으로 추측해서 요약합니다.
"""


async def summarize(title: str, body: str) -> list[str]:
    """
    게시물 제목과 본문을 받아 3줄 한국어 요약을 반환합니다.
    실패 시 빈 리스트 대신 제목 기반 fallback을 반환합니다.
    """
    content_part = f"\n\n본문:\n{body[:3000]}" if body.strip() else ""
    prompt = f"제목: {title}{content_part}"

    try:
        resp = await _client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        for key in ("summary", "summaries", "lines", "result"):
            if key in parsed and isinstance(parsed[key], list):
                return [s for s in parsed[key][:3] if s]
        # 첫 번째 list 값 사용
        for v in parsed.values():
            if isinstance(v, list) and v:
                return [s for s in v[:3] if s]
        return _fallback(title)
    except Exception:
        return _fallback(title)


def _fallback(title: str) -> list[str]:
    return [
        f"'{title}' 이슈가 커뮤니티에서 주목받고 있어요.",
        "네티즌들 사이에서 다양한 의견이 오가고 있어요.",
        "자세한 내용은 원문 링크를 확인해 보세요.",
    ]
