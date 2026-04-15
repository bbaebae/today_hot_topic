// Vercel Edge Function: Zum 실시간 검색어 → JSON 프록시
// Edge Runtime은 DOMParser 미지원 → regex로 HTML 파싱
export const config = { runtime: 'edge' };

const ZUM_URL = 'https://zum.com/';
const ZUM_REALTIME_URL = 'https://api2.zum.com/zum-main/v2/realtime/keyword';

const HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 ' +
    '(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
  Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'ko-KR,ko;q=0.9',
  Referer: 'https://zum.com/',
};

interface TrendingResponse {
  keywords: string[];
  updatedAt: string;
}

export default async function handler(): Promise<Response> {
  try {
    // 1차: Zum 내부 API 시도 (JSON)
    let keywords = await fetchFromZumApi();

    // 2차: HTML 스크래핑 fallback
    if (keywords.length === 0) {
      keywords = await fetchFromZumHtml();
    }

    const body: TrendingResponse = {
      keywords,
      updatedAt: new Date().toISOString(),
    };

    return new Response(JSON.stringify(body), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 's-maxage=300, stale-while-revalidate=60',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'unknown error';
    return new Response(
      JSON.stringify({ error: message, keywords: [], updatedAt: new Date().toISOString() }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      }
    );
  }
}

/** Zum 내부 JSON API — 실패 시 빈 배열 반환 */
async function fetchFromZumApi(): Promise<string[]> {
  try {
    const res = await fetch(ZUM_REALTIME_URL, {
      headers: { ...HEADERS, Accept: 'application/json' },
    });
    if (!res.ok) return [];

    // 예상 구조: { result: { realtimeKeywords: [{ keyword, rank }, ...] } }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = (await res.json()) as any;
    const list: { keyword?: string; word?: string }[] =
      data?.result?.realtimeKeywords ??
      data?.data?.keywords ??
      data?.keywords ??
      [];

    const keywords = list
      .map((item) => (item.keyword ?? item.word ?? '').trim())
      .filter(Boolean)
      .slice(0, 10);

    return keywords;
  } catch {
    return [];
  }
}

/** Zum 메인 페이지 HTML 스크래핑 */
async function fetchFromZumHtml(): Promise<string[]> {
  const res = await fetch(ZUM_URL, { headers: HEADERS });
  if (!res.ok) throw new Error(`Zum fetch failed: ${res.status}`);

  const html = await res.text();
  return parseZumKeywords(html);
}

/**
 * Zum HTML에서 실시간 검색어 추출.
 *
 * 후보 패턴:
 *   1. <span class="keyword">검색어</span>  (realtime-keyword 컴포넌트)
 *   2. data-keyword="검색어" 속성
 *   3. realtime_search 섹션 내 <a> 텍스트
 */
function parseZumKeywords(html: string): string[] {
  const keywords: string[] = [];
  const seen = new Set<string>();

  const add = (kw: string) => {
    const k = kw.trim();
    if (k && k.length >= 2 && !seen.has(k)) {
      seen.add(k);
      keywords.push(k);
    }
  };

  // 패턴 1: data-keyword 속성
  for (const m of html.matchAll(/data-keyword="([^"]+)"/g)) {
    add(decodeHtmlEntities(m[1]));
    if (keywords.length >= 10) return keywords;
  }

  // 패턴 2: <span class="keyword">...</span>
  for (const m of html.matchAll(/<span[^>]+class="[^"]*keyword[^"]*"[^>]*>([^<]{2,30})<\/span>/g)) {
    add(decodeHtmlEntities(m[1]));
    if (keywords.length >= 10) return keywords;
  }

  // 패턴 3: realtime / trend 관련 섹션 내 <a> 텍스트
  const sectionMatch = html.match(
    /(?:realtime|trend|ranking)[\s\S]{0,3000}?<\/(?:section|div|ul)>/i
  );
  if (sectionMatch) {
    for (const m of sectionMatch[0].matchAll(/<a[^>]*>([^<]{2,30})<\/a>/g)) {
      const text = decodeHtmlEntities(m[1]).trim();
      // 숫자/순위만 있는 텍스트 제외
      if (/^[\d\s위]+$/.test(text)) continue;
      add(text);
      if (keywords.length >= 10) return keywords;
    }
  }

  return keywords;
}

function decodeHtmlEntities(str: string): string {
  return str
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ');
}
