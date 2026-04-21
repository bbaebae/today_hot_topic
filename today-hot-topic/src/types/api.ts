import type { Topic, TopicDetail } from './topic';
import type { User } from './user';

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
}

export type { Topic, TopicDetail, User };
