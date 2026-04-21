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
  return get('/users/me');
}
