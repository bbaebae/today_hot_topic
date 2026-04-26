import { USE_MOCK, delay, post } from './api';

export async function fetchUserProfile() {
  if (USE_MOCK) {
    await delay(300);
    return {
      user: {
        id: 'mock-user-id',
        tossUserId: 'mock-toss-user',
        isPremium: false,
        totalPoints: 0,
        createdAt: new Date().toISOString(),
      },
    };
  }

  const { get } = await import('./api');
  try {
    return get('/users/me');
  } catch (e: unknown) {
    // 토스 앱 외부(브라우저 등) 환경에서 JWT 없이 401이 오면 null 유저로 처리
    if (e instanceof Error && (e as Error & { status?: number }).status === 401) {
      return { user: null };
    }
    throw e;
  }
}

export async function recordAdWatched(): Promise<{ total_points: number; earned: number }> {
  if (USE_MOCK) {
    await delay(200);
    return { total_points: 10, earned: 10 };
  }
  return post('/rewards/ad-watched', {});
}

export async function convertToTossPoints(amount: number): Promise<{ total_points: number; converted: number }> {
  if (USE_MOCK) {
    await delay(800);
    return { total_points: 0, converted: amount };
  }
  return post('/rewards/convert', { amount });
}
