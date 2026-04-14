import type { TrendingKeyword } from '../types/topic';
import { mockTrendingKeywords } from '../mocks/trending';
import { USE_MOCK } from './api';

const PREV_RANKS_KEY = 'trending_prev_ranks';
const CACHE_KEY = 'trending_cache';
const CACHE_TTL_MS = 5 * 60 * 1000; // 5분

interface CachedTrending {
  keywords: TrendingKeyword[];
  cachedAt: number;
}

function getChangeIndicator(
  keyword: string,
  rank: number,
  prevRanks: Record<string, number>
): TrendingKeyword['change'] {
  if (!(keyword in prevRanks)) return 'new';
  const prev = prevRanks[keyword];
  if (prev > rank) return 'up';
  if (prev < rank) return 'down';
  return 'same';
}

function saveCurrentRanks(keywords: TrendingKeyword[]) {
  const currentRanks: Record<string, number> = {};
  keywords.forEach(({ keyword, rank }) => {
    currentRanks[keyword] = rank;
  });
  localStorage.setItem(PREV_RANKS_KEY, JSON.stringify(currentRanks));
}

function getPrevRanks(): Record<string, number> {
  try {
    return JSON.parse(localStorage.getItem(PREV_RANKS_KEY) ?? '{}') as Record<string, number>;
  } catch {
    return {};
  }
}

function getCached(): TrendingKeyword[] | null {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const cached = JSON.parse(raw) as CachedTrending;
    if (Date.now() - cached.cachedAt > CACHE_TTL_MS) return null;
    return cached.keywords;
  } catch {
    return null;
  }
}

function setCache(keywords: TrendingKeyword[]) {
  try {
    const data: CachedTrending = { keywords, cachedAt: Date.now() };
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    // 스토리지 용량 초과 시 무시
  }
}

export async function fetchTrendingKeywords(): Promise<TrendingKeyword[]> {
  if (USE_MOCK) {
    return mockTrendingKeywords;
  }

  // 세션 캐시 hit
  const cached = getCached();
  if (cached) return cached;

  const res = await fetch('/api/trending');
  if (!res.ok) throw new Error(`trending fetch failed: ${res.status}`);

  const data = (await res.json()) as { keywords: string[] };
  const prevRanks = getPrevRanks();

  const keywords: TrendingKeyword[] = data.keywords.map((keyword, i) => ({
    rank: i + 1,
    keyword,
    change: getChangeIndicator(keyword, i + 1, prevRanks),
  }));

  saveCurrentRanks(keywords);
  setCache(keywords);

  return keywords;
}
