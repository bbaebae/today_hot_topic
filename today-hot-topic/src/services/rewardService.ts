import type { RewardResponse } from '../types/api';
import type { RewardType } from '../types/user';
import { USE_MOCK, delay, post } from './api';

const DAILY_MAX_COUNT = 3;
const REWARD_COUNT_KEY = 'reward_count';
const REWARD_DATE_KEY = 'reward_date';
const REWARD_BALANCE_KEY = 'reward_balance';

function getTodayStr() {
  return new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"
}

function getMockRewardCount(): number {
  const savedDate = localStorage.getItem(REWARD_DATE_KEY);
  if (savedDate !== getTodayStr()) {
    localStorage.setItem(REWARD_DATE_KEY, getTodayStr());
    localStorage.setItem(REWARD_COUNT_KEY, '0');
    return 0;
  }
  return parseInt(localStorage.getItem(REWARD_COUNT_KEY) ?? '0', 10);
}

function getMockBalance(): number {
  return parseInt(localStorage.getItem(REWARD_BALANCE_KEY) ?? '1230', 10);
}

export async function claimReward(
  rewardType: RewardType,
  referenceId: string
): Promise<RewardResponse> {
  if (USE_MOCK) {
    await delay(600);

    const count = getMockRewardCount();
    if (count >= DAILY_MAX_COUNT) {
      const err = new Error('오늘의 포인트 지급 한도에 도달했습니다.');
      Object.assign(err, { status: 429, body: { error: 'DAILY_LIMIT_EXCEEDED' } });
      throw err;
    }

    // 1~9 사이 랜덤 포인트
    const amount = Math.floor(Math.random() * 9) + 1;
    const newCount = count + 1;
    const newBalance = getMockBalance() + amount;

    localStorage.setItem(REWARD_COUNT_KEY, String(newCount));
    localStorage.setItem(REWARD_BALANCE_KEY, String(newBalance));

    return {
      transactionId: `tx-${Date.now()}`,
      amount,
      status: 'success',
      currentBalance: newBalance,
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
