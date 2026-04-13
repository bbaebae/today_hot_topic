import type { Topic, TopicDetail, Category } from '../types/topic';
import type { TopicsResponse } from '../types/api';
import { USE_MOCK, delay, get } from './api';
import { mockTopics, mockTopicDetails } from '../mocks/topics';

export async function fetchTopics(category?: Category): Promise<Topic[]> {
  if (USE_MOCK) {
    await delay(400);
    if (!category) return mockTopics.slice().sort((a, b) => b.viewCount - a.viewCount);
    return mockTopics
      .filter((t) => t.category === category)
      .sort((a, b) => a.rank - b.rank);
  }

  const params = new URLSearchParams();
  if (category) params.set('category', category);
  const data = await get<TopicsResponse>(`/topics?${params.toString()}`);
  return data.topics;
}

export async function fetchTopicDetail(id: string): Promise<TopicDetail> {
  if (USE_MOCK) {
    await delay(300);
    const detail = mockTopicDetails[id];
    if (!detail) {
      // 상세 데이터가 없는 경우 기본 토픽에서 생성
      const topic = mockTopics.find((t) => t.id === id);
      if (!topic) throw new Error('Topic not found');
      return {
        ...topic,
        sourceUrl: 'https://pann.nate.com',
        summary: [
          '첫 번째 AI 요약 문장입니다. 이슈의 핵심 내용을 간결하게 담았어요.',
          '두 번째 AI 요약 문장입니다. 상황의 배경과 맥락을 설명해요.',
          '세 번째 AI 요약 문장입니다. 커뮤니티의 주요 반응을 정리했어요.',
        ],
        poll: {
          id: `poll-${id}`,
          topicId: id,
          optionAText: '찬성',
          optionBText: '반대',
          optionACount: Math.floor(Math.random() * 5000 + 1000),
          optionBCount: Math.floor(Math.random() * 5000 + 1000),
          userVoted: null,
        },
      };
    }
    return detail;
  }

  return get<TopicDetail>(`/topics/${id}`);
}
