export type Category = 'news' | 'story' | 'finance';

export interface Topic {
  id: string;
  title: string;
  category: Category;
  imageUrl: string | null;
  viewCount: number;
  rank: number;
  createdAt: string;
}

export interface TopicDetail extends Topic {
  sourceUrl: string;
  summary: string[];
  poll: Poll;
}

export interface Poll {
  id: string;
  topicId: string;
  optionAText: string;
  optionBText: string;
  optionACount: number;
  optionBCount: number;
  userVoted: 'A' | 'B' | null;
}
