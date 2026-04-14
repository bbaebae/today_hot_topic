// Vercel Edge Function: Google Trends 한국 실시간 검색어 RSS → JSON 프록시
// Edge Runtime은 글로벌 배포 + 빠른 콜드스타트 + Fetch API 네이티브 지원
export const config = { runtime: 'edge' };

const TRENDS_RSS_URL =
  'https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR';

interface TrendingResponse {
  keywords: string[];
  updatedAt: string;
}

export default async function handler(): Promise<Response> {
  try {
    const res = await fetch(TRENDS_RSS_URL, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (compatible; TrendFetcher/1.0; +https://github.com)',
        Accept: 'application/rss+xml, application/xml, text/xml',
      },
      // Edge Runtime에서는 cache 옵션으로 CDN 캐시 제어
      // @ts-expect-error — Next.js 확장 옵션
      next: { revalidate: 300 },
    });

    if (!res.ok) {
      throw new Error(`RSS fetch failed: ${res.status}`);
    }

    const xml = await res.text();
    const keywords = parseKeywords(xml);

    const body: TrendingResponse = {
      keywords,
      updatedAt: new Date().toISOString(),
    };

    return new Response(JSON.stringify(body), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        // Vercel CDN 캐시 5분, stale-while-revalidate 60초
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

/**
 * Google Trends RSS XML에서 <item> 내 <title>을 최대 10개 추출합니다.
 *
 * RSS 구조 예시:
 *   <item>
 *     <title><![CDATA[검색어]]></title>
 *     <ht:approx_traffic>500K+</ht:approx_traffic>
 *     ...
 *   </item>
 */
function parseKeywords(xml: string): string[] {
  const keywords: string[] = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let itemMatch: RegExpExecArray | null;

  while ((itemMatch = itemRegex.exec(xml)) !== null && keywords.length < 10) {
    const item = itemMatch[1];
    // CDATA 형식과 일반 형식 모두 처리
    const titleMatch =
      item.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>/) ??
      item.match(/<title>(.*?)<\/title>/);

    const keyword = titleMatch?.[1]?.trim();
    if (keyword) keywords.push(keyword);
  }

  return keywords;
}
