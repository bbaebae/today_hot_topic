import { useState, useEffect, useCallback } from 'react';
import type { Topic, Category } from '../types/topic';
import { fetchTopics } from '../services/topicService';

const CATEGORY_KEY = 'home_category';

function getSavedCategory(fallback: Category): Category {
  return (sessionStorage.getItem(CATEGORY_KEY) as Category) ?? fallback;
}

export function useTopics(initialCategory: Category = 'story') {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setRawCategory] = useState<Category>(() => getSavedCategory(initialCategory));

  const setCategory = useCallback((cat: Category) => {
    sessionStorage.setItem(CATEGORY_KEY, cat);
    setRawCategory(cat);
  }, []);

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
