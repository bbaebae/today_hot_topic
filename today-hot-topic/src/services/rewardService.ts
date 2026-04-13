import type { RewardResponse } from '../types/api';
import type { RewardType } from '../types/user';
import { USE_MOCK, delay, post } from './api';

const DAILY_LIMIT = 100;
let mockTodayEarned = 30;

export async function claimReward(
  rewardType: RewardType,
  referenceId: string
): Promise<RewardResponse> {
  if (USE_MOCK) {
    await delay(600);

    const amount = rewardType === 'ad' ? 20 : 10;

    if (mockTodayEarned + amount > DAILY_LIMIT) {
      const err = new Error('오늘의 포인트 지급 한도에 도달했습니다.');
      Object.assign(err, { status: 429, body: { error: 'DAILY_LIMIT_EXCEEDED' } });
      throw err;
    }

    mockTodayEarned += amount;

    return {
      transactionId: `tx-${Date.now()}`,
      amount,
      status: 'success',
      currentBalance: 1230 + mockTodayEarned,
    };
  }

  return post<RewardResponse, { reward_type: RewardType; reference_id: string }>(
    '/rewards/claim',
    { reward_type: rewardType, reference_id: referenceId }
  );
}

export async function fetchUserProfile() {
  if (USE_MOCK) {
    await delay(300);
    const { mockUser, mockTransactions } = await import('../mocks/user');
    return { user: mockUser, transactions: mockTransactions };
  }

  const { get } = await import('./api');
  return get('/users/me');
}
