export type MainTab = 'story' | 'news';
export type NewsSubCategory = 'society' | 'economy' | 'sports' | 'love';
export type Category = 'story' | 'society' | 'economy' | 'sports' | 'love';

export interface TrendingKeyword {
  rank: number;
  keyword: string;
  change: 'up' | 'down' | 'new' | 'same';
}

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
  body: string;
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
