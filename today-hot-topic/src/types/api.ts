import type { Topic, TopicDetail } from './topic';
import type { User, PointTransaction } from './user';

export interface TopicsResponse {
  topics: Topic[];
  total: number;
  page: number;
  limit: number;
}

export interface VoteResponse {
  pollId: string;
  selectedOption: 'A' | 'B';
  optionACount: number;
  optionBCount: number;
  rewardEligible: boolean;
}

export interface RewardResponse {
  transactionId: string;
  amount: number;
  status: 'success' | 'failed';
  currentBalance: number;
}

export interface UserResponse extends User {
  transactions: PointTransaction[];
}

export type { Topic, TopicDetail, User, PointTransaction };
