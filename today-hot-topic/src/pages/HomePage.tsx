import { useNavigate } from 'react-router-dom';
import { useTopics } from '../hooks/useTopics';
import { CategoryTab } from '../components/home/CategoryTab';
import { TopicItem } from '../components/home/TopicItem';
import { TopicSkeleton } from '../components/home/TopicSkeleton';
import type { Category } from '../types/topic';
import styles from './HomePage.module.css';

export default function HomePage() {
  const navigate = useNavigate();
  const { topics, isLoading, category, setCategory, refresh } = useTopics('story');

  const handleCategoryChange = (cat: Category) => {
    setCategory(cat);
  };

  // Pull-to-refresh 간이 구현 (버튼으로 대체)
  const handleRefresh = () => {
    refresh();
  };

  return (
    <div className={styles.page}>
      {/* 헤더 */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <h1 className={styles.logo}>오늘 왜 떠?</h1>
          <button className={styles.refreshBtn} onClick={handleRefresh} aria-label="새로고침">
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
        <CategoryTab selected={category} onChange={handleCategoryChange} />
      </header>

      {/* 리스트 */}
      <div className={styles.listArea}>
        {isLoading ? (
          <TopicSkeleton count={8} />
        ) : topics.length === 0 ? (
          <div className={styles.empty}>
            <p>지금은 핫토픽이 없어요 🤔</p>
            <button onClick={handleRefresh}>다시 불러오기</button>
          </div>
        ) : (
          <ul className={styles.topicList}>
            {topics.map((topic) => (
              <TopicItem
                key={topic.id}
                topic={topic}
                onClick={() => navigate(`/topics/${topic.id}`)}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
