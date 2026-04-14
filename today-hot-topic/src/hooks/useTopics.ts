import { useState, useEffect, useCallback } from 'react';
import type { Topic, Category, MainTab, NewsSubCategory } from '../types/topic';
import { fetchTopics } from '../services/topicService';

const MAIN_TAB_KEY = 'home_main_tab';
const NEWS_SUB_KEY = 'home_news_sub';

function getSavedMainTab(fallback: MainTab): MainTab {
  return (sessionStorage.getItem(MAIN_TAB_KEY) as MainTab) ?? fallback;
}

function getSavedNewsSubCategory(fallback: NewsSubCategory): NewsSubCategory {
  return (sessionStorage.getItem(NEWS_SUB_KEY) as NewsSubCategory) ?? fallback;
}

export function useTopics(initialMainTab: MainTab = 'story') {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mainTab, setRawMainTab] = useState<MainTab>(() => getSavedMainTab(initialMainTab));
  const [newsSubCategory, setRawNewsSubCategory] = useState<NewsSubCategory>(() =>
    getSavedNewsSubCategory('society')
  );

  const effectiveCategory: Category = mainTab === 'story' ? 'story' : newsSubCategory;

  const setMainTab = useCallback((tab: MainTab) => {
    sessionStorage.setItem(MAIN_TAB_KEY, tab);
    setRawMainTab(tab);
  }, []);

  const setNewsSubCategory = useCallback((sub: NewsSubCategory) => {
    sessionStorage.setItem(NEWS_SUB_KEY, sub);
    setRawNewsSubCategory(sub);
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
    void load(effectiveCategory);
  }, [effectiveCategory, load]);

  const refresh = useCallback(() => {
    void load(effectiveCategory);
  }, [effectiveCategory, load]);

  return {
    topics,
    isLoading,
    error,
    mainTab,
    setMainTab,
    newsSubCategory,
    setNewsSubCategory,
    effectiveCategory,
    refresh,
  };
}
