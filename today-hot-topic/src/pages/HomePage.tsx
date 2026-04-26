import { Fragment, useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTopics } from '../hooks/useTopics';
import { useProfile } from '../hooks/useProfile';
import { useFullScreenAd } from '../hooks/useFullScreenAd';
import { useRewardedAd } from '../hooks/useRewardedAd';
import { CategoryTab } from '../components/home/CategoryTab';
import { NewsSubTab } from '../components/home/NewsSubTab';
import { TrendingSection } from '../components/home/TrendingSection';
import { TopicItem } from '../components/home/TopicItem';
import { TopicSkeleton } from '../components/home/TopicSkeleton';
import { BannerAdItem } from '../components/home/BannerAdItem';
import type { MainTab, NewsSubCategory } from '../types/topic';
import styles from './HomePage.module.css';

const PAGE_SIZE = 5;
const SS_VISIBLE = 'home_visible_count';
const SS_SCROLL = 'home_scroll_top';

export default function HomePage() {
  const navigate = useNavigate();
  const { user, refetch: refetchProfile } = useProfile();
  const { maybeShow } = useFullScreenAd();
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const [visibleCount, setVisibleCount] = useState(() => {
    const saved = sessionStorage.getItem(SS_VISIBLE);
    return saved ? parseInt(saved, 10) : PAGE_SIZE;
  });
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [earnedToast, setEarnedToast] = useState<string | null>(null);

  const {
    topics,
    isLoading,
    mainTab,
    setMainTab,
    newsSubCategory,
    setNewsSubCategory,
    refresh,
  } = useTopics('story');

  // visibleCount 변경 시 저장
  useEffect(() => {
    sessionStorage.setItem(SS_VISIBLE, String(visibleCount));
  }, [visibleCount]);

  // 데이터 로드 완료 후 스크롤 복원
  useEffect(() => {
    if (!isLoading && scrollAreaRef.current) {
      const saved = sessionStorage.getItem(SS_SCROLL);
      if (saved) {
        scrollAreaRef.current.scrollTop = parseInt(saved, 10);
        sessionStorage.removeItem(SS_SCROLL);
      }
    }
  }, [isLoading]);

  // 카테고리 변경 시 표시 개수 초기화
  const handleMainTabChange = (tab: MainTab) => {
    setVisibleCount(PAGE_SIZE);
    sessionStorage.removeItem(SS_SCROLL);
    sessionStorage.removeItem(SS_VISIBLE);
    setMainTab(tab);
  };

  const handleNewsSubChange = (sub: NewsSubCategory) => {
    setVisibleCount(PAGE_SIZE);
    sessionStorage.removeItem(SS_SCROLL);
    sessionStorage.removeItem(SS_VISIBLE);
    setNewsSubCategory(sub);
  };

  const handleTopicClick = (topicId: string) => {
    if (scrollAreaRef.current) {
      sessionStorage.setItem(SS_SCROLL, String(scrollAreaRef.current.scrollTop));
    }
    maybeShow(() => navigate(`/topics/${topicId}`), user?.isPremium ?? false);
  };

  const showToast = (msg: string) => {
    setEarnedToast(msg);
    setTimeout(() => setEarnedToast(null), 2500);
  };

  const onPointsEarned = useCallback((points: number) => {
    refetchProfile();
    showToast(`+${points}P 적립!`);
  }, [refetchProfile]);

  const { showAd } = useRewardedAd(onPointsEarned);

  const handleLoadMore = () => {
    setIsLoadingMore(true);
    showAd(() => {
      setVisibleCount((prev) => prev + PAGE_SIZE);
      setIsLoadingMore(false);
    });
  };

  const visibleTopics = topics.slice(0, visibleCount);
  const hasMore = topics.length > visibleCount;

  return (
    <div className={styles.page}>
      {/* 포인트 적립 토스트 */}
      {earnedToast && (
        <div className={styles.toast}>{earnedToast}</div>
      )}

      {/* 헤더 */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.logo}>오늘 왜 떠?</h1>
          <button className={styles.refreshBtn} onClick={refresh} aria-label="새로고침">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M1 4v6h6M23 20v-6h-6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M20.49 9A9 9 0 005.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 013.51 15"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </header>

      {/* 스크롤 영역 */}
      <div className={styles.scrollArea} ref={scrollAreaRef}>
        {/* 실시간 검색어 */}
        <TrendingSection />

        {/* 메인 탭 (썰 / 뉴스) — sticky */}
        <div className={styles.stickyTabs}>
          <CategoryTab selected={mainTab} onChange={handleMainTabChange} />

          {/* 뉴스 서브탭 */}
          {mainTab === 'news' && (
            <NewsSubTab selected={newsSubCategory} onChange={handleNewsSubChange} />
          )}
        </div>

        {/* 토픽 리스트 */}
        {isLoading ? (
          <TopicSkeleton count={PAGE_SIZE} />
        ) : topics.length === 0 ? (
          <div className={styles.empty}>
            <p>지금은 핫토픽이 없어요 🤔</p>
            <button onClick={refresh}>다시 불러오기</button>
          </div>
        ) : (
          <>
            <ul className={styles.topicList}>
              {visibleTopics.map((topic, index) => (
                <Fragment key={topic.id}>
                  <TopicItem
                    topic={topic}
                    onClick={() => handleTopicClick(topic.id)}
                  />
                  {(index + 1) % 4 === 0 && index < visibleCount - 1 && (
                    <BannerAdItem key={`banner-${index}`} />
                  )}
                </Fragment>
              ))}
            </ul>

            {hasMore && (
              <div className={styles.loadMoreWrapper}>
                <button
                  className={styles.loadMoreBtn}
                  onClick={handleLoadMore}
                  disabled={isLoadingMore}
                >
                  {isLoadingMore ? (
                    '광고 로딩 중...'
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <circle
                          cx="12" cy="12" r="10"
                          stroke="currentColor" strokeWidth="2"
                        />
                        <path
                          d="M12 8v8M8 12h8"
                          stroke="currentColor" strokeWidth="2"
                          strokeLinecap="round"
                        />
                      </svg>
                      광고 보고 더보기
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
