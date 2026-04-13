import type { User, PointTransaction } from '../types/user';

export const mockUser: User = {
  id: 'user-mock-001',
  tossUserId: 'toss_mock_12345',
  isPremium: false,
  totalPoints: 1230,
  todayEarned: 30,
  createdAt: '2026-01-01T00:00:00Z',
};

export const mockTransactions: PointTransaction[] = [
  {
    id: 'tx-001',
    amount: 10,
    reason: 'vote',
    status: 'success',
    createdAt: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
  },
  {
    id: 'tx-002',
    amount: 10,
    reason: 'vote',
    status: 'success',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'tx-003',
    amount: 20,
    reason: 'ad',
    status: 'success',
    createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'tx-004',
    amount: 10,
    reason: 'vote',
    status: 'success',
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'tx-005',
    amount: 10,
    reason: 'share',
    status: 'success',
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'tx-006',
    amount: 20,
    reason: 'ad',
    status: 'success',
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'tx-007',
    amount: 10,
    reason: 'vote',
    status: 'success',
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
  },
];
