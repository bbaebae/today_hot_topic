import { Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTopics } from '../hooks/useTopics';
import { useProfile } from '../hooks/useProfile';
import { useFullScreenAd } from '../hooks/useFullScreenAd';
import { CategoryTab } from '../components/home/CategoryTab';
import { NewsSubTab } from '../components/home/NewsSubTab';
import { TrendingSection } from '../components/home/TrendingSection';
import { TopicItem } from '../components/home/TopicItem';
import { TopicSkeleton } from '../components/home/TopicSkeleton';
import { BannerAdItem } from '../components/home/BannerAdItem';
import type { MainTab, NewsSubCategory } from '../types/topic';
import styles from './HomePage.module.css';

export default function HomePage() {
  const navigate = useNavigate();
  const { user } = useProfile();
  const { show: showAd } = useFullScreenAd();
  const {
    topics,
    isLoading,
    mainTab,
    setMainTab,
    newsSubCategory,
    setNewsSubCategory,
    refresh,
  } = useTopics('story');

  const handleMainTabChange = (tab: MainTab) => {
    setMainTab(tab);
  };

  const handleNewsSubChange = (sub: NewsSubCategory) => {
    setNewsSubCategory(sub);
  };

  const handleTopicClick = (topicId: string) => {
    // 프리미엄 유저는 광고 없이 바로 이동
    showAd(() => navigate(`/topics/${topicId}`), user?.isPremium ?? false);
  };

  return (
    <div className={styles.page}>
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
      <div className={styles.scrollArea}>
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
          <TopicSkeleton count={8} />
        ) : topics.length === 0 ? (
          <div className={styles.empty}>
            <p>지금은 핫토픽이 없어요 🤔</p>
            <button onClick={refresh}>다시 불러오기</button>
          </div>
        ) : (
          <ul className={styles.topicList}>
            {topics.map((topic, index) => (
              <Fragment key={topic.id}>
                <TopicItem
                  topic={topic}
                  onClick={() => handleTopicClick(topic.id)}
                />
                {(index + 1) % 5 === 0 && <BannerAdItem key={`banner-${index}`} />}
              </Fragment>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
