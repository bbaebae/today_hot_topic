// Vercel Edge Function: Zum 실시간 검색어 → JSON 프록시
// Edge Runtime은 DOMParser 미지원 → regex로 HTML 파싱
export const config = { runtime: 'edge' };

const ZUM_URL = 'https://zum.com/';
const ZUM_REALTIME_URL = 'https://api2.zum.com/zum-main/v2/realtime/keyword';
const DAUM_MOBILE_URL = 'https://m.daum.net/';
const GOOGLE_TRENDS_URL =
  'https://trends.google.com/trending/rss?geo=KR&sort=search-volume';

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
  source: string;
  updatedAt: string;
}

export default async function handler(): Promise<Response> {
  // 1차: Zum 내부 JSON API
  let keywords = await fetchFromZumApi();
  let source = 'zum-api';

  // 2차: Zum HTML 스크래핑
  if (keywords.length === 0) {
    keywords = await fetchFromZumHtml();
    source = 'zum-html';
  }

  // 3차: 다음 모바일 HTML
  if (keywords.length === 0) {
    keywords = await fetchFromDaum();
    source = 'daum';
  }

  // 4차: Google Trends fallback
  if (keywords.length === 0) {
    keywords = await fetchFromGoogleTrends();
    source = 'google-trends';
  }

  const body: TrendingResponse = {
    keywords,
    source,
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
}

/** Zum 내부 JSON API — 실패 시 빈 배열 반환 */
async function fetchFromZumApi(): Promise<string[]> {
  try {
    const res = await fetch(ZUM_REALTIME_URL, {
      headers: { ...HEADERS, Accept: 'application/json' },
    });
    if (!res.ok) return [];

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = (await res.json()) as any;
    const list: { keyword?: string; word?: string }[] =
      data?.result?.realtimeKeywords ??
      data?.data?.keywords ??
      data?.keywords ??
      [];

    return list
      .map((item) => (item.keyword ?? item.word ?? '').trim())
      .filter(Boolean)
      .slice(0, 10);
  } catch {
    return [];
  }
}

/** Zum 메인 페이지 HTML 스크래핑 — 실패 시 빈 배열 반환 */
async function fetchFromZumHtml(): Promise<string[]> {
  try {
    const res = await fetch(ZUM_URL, { headers: HEADERS });
    if (!res.ok) return [];

    const html = await res.text();
    return parseZumKeywords(html);
  } catch {
    return [];
  }
}

/** 다음 모바일 실시간 트렌드 — 실패 시 빈 배열 반환 */
async function fetchFromDaum(): Promise<string[]> {
  try {
    const res = await fetch(DAUM_MOBILE_URL, {
      headers: {
        ...HEADERS,
        Referer: 'https://m.daum.net/',
      },
    });
    if (!res.ok) return [];

    const html = await res.text();
    return parseDaumKeywords(html);
  } catch {
    return [];
  }
}

/**
 * 다음 모바일 HTML에서 실시간 트렌드 추출.
 * 구조: href="...DA=RT1...&q=키워드" (list_trendrank 섹션)
 */
function parseDaumKeywords(html: string): string[] {
  const keywords: string[] = [];
  const seen = new Set<string>();

  // DA=RT{n} 패턴으로 실시간 트렌드 링크만 추출
  const matches = html.matchAll(/DA=RT\d[^"]*?[?&]q=([^"&\s]+)/g);
  for (const m of matches) {
    const kw = decodeURIComponent(m[1].replace(/\+/g, ' ')).trim();
    if (kw && kw.length >= 2 && !seen.has(kw)) {
      seen.add(kw);
      keywords.push(kw);
    }
    if (keywords.length >= 10) break;
  }

  return keywords;
}

/** Google Trends RSS fallback — 실패 시 빈 배열 반환 */
async function fetchFromGoogleTrends(): Promise<string[]> {
  try {
    const res = await fetch(GOOGLE_TRENDS_URL, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; TrendFetcher/1.0)',
        Accept: 'application/rss+xml, application/xml, text/xml',
      },
    });
    if (!res.ok) return [];

    const xml = await res.text();
    const keywords: string[] = [];
    const itemRegex = /<item>([\s\S]*?)<\/item>/g;
    let m: RegExpExecArray | null;

    while ((m = itemRegex.exec(xml)) !== null && keywords.length < 10) {
      const titleMatch =
        m[1].match(/<title><!\[CDATA\[(.*?)\]\]><\/title>/) ??
        m[1].match(/<title>(.*?)<\/title>/);
      const kw = titleMatch?.[1]?.trim();
      if (kw) keywords.push(kw);
    }

    return keywords;
  } catch {
    return [];
  }
}

/**
 * Zum HTML에서 실시간 검색어 추출.
 * 구조: <span class="issue-word-list__keyword">검색어</span>
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

  // 1순위: issue-word-list__keyword 클래스 (zum.com 실시간 트렌드)
  for (const m of html.matchAll(/<span[^>]+class="issue-word-list__keyword"[^>]*>([^<]+)<\/span>/g)) {
    add(decodeHtmlEntities(m[1]));
    if (keywords.length >= 10) return keywords;
  }

  // 2순위: data-keyword 속성
  for (const m of html.matchAll(/data-keyword="([^"]+)"/g)) {
    add(decodeHtmlEntities(m[1]));
    if (keywords.length >= 10) return keywords;
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
