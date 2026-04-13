export interface User {
  id: string;
  tossUserId: string;
  isPremium: boolean;
  totalPoints: number;
  todayEarned: number;
  createdAt: string;
}

export type RewardType = 'vote' | 'ad' | 'share';

export interface PointTransaction {
  id: string;
  amount: number;
  reason: RewardType;
  status: 'pending' | 'success' | 'failed';
  createdAt: string;
}
