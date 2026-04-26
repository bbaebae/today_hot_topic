import { useState, useEffect } from 'react';
import { safeStorage } from '../utils/toss';
import type { TopicDetail } from '../types/topic';
import { fetchTopicDetail } from '../services/topicService';

const detailCache = new Map<string, TopicDetail>();

export function useTopicDetail(topicId: string) {
  const [topic, setTopic] = useState<TopicDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [votedOption, setVotedOption] = useState<'A' | 'B' | null>(null);

  // 투표 상태 Storage에서 복원
  useEffect(() => {
    safeStorage.getItem(`voted_${topicId}`)
      .then((v) => {
        if (v === 'A' || v === 'B') setVotedOption(v);
      })
      .catch(() => null);
  }, [topicId]);

  useEffect(() => {
    let cancelled = false;
    setError(null);

    const cached = detailCache.get(topicId);
    if (cached) {
      setTopic(cached);
      setIsLoading(false);
    } else {
      setIsLoading(true);
      setTopic(null);
    }

    fetchTopicDetail(topicId)
      .then((data) => {
        if (!cancelled) {
          detailCache.set(topicId, data);
          setTopic(data);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : '불러오기 실패');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [topicId]);

  const markVoted = (option: 'A' | 'B') => {
    setVotedOption(option);
    void safeStorage.setItem(`voted_${topicId}`, option);
    // 투표 결과 로컬 업데이트
    if (topic) {
      setTopic((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          poll: {
            ...prev.poll,
            userVoted: option,
            optionACount: option === 'A' ? prev.poll.optionACount + 1 : prev.poll.optionACount,
            optionBCount: option === 'B' ? prev.poll.optionBCount + 1 : prev.poll.optionBCount,
          },
        };
      });
    }
  };

  return {
    topic,
    isLoading,
    error,
    hasVoted: votedOption !== null,
    votedOption,
    markVoted,
  };
}
