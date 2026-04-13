import { useState, useEffect, useCallback } from 'react';
import type { Topic, Category } from '../types/topic';
import { fetchTopics } from '../services/topicService';

export function useTopics(initialCategory: Category = 'story') {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<Category>(initialCategory);

  const load = useCallback(async (cat: Category) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchTopics(cat);
      setTopics(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : '불러오기 실패');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(category);
  }, [category, load]);

  const refresh = useCallback(() => {
    void load(category);
  }, [category, load]);

  return { topics, isLoading, error, category, setCategory, refresh };
}
