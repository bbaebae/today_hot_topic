import { USE_MOCK, delay } from './api';

export async function fetchUserProfile() {
  if (USE_MOCK) {
    await delay(300);
    return {
      user: {
        id: 'mock-user-id',
        tossUserId: 'mock-toss-user',
        isPremium: false,
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
