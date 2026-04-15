import { useState, useEffect } from 'react';
import { fetchTrendingKeywords } from '../../services/trendingService';
import { safeOpenUrl } from '../../utils/toss';
import type { TrendingKeyword } from '../../types/topic';
import styles from './TrendingSection.module.css';

function ChangeIndicator({ change }: { change: TrendingKeyword['change'] }) {
  if (change === 'new') return <span className={styles.badgeNew}>NEW</span>;
  if (change === 'up') return <span className={styles.arrowUp}>▲</span>;
  if (change === 'down') return <span className={styles.arrowDown}>▼</span>;
  return <span className={styles.arrowSame}>–</span>;
}

function formatUpdateTime(iso: string): string {
  const d = new Date(iso);
  const h = d.getHours().toString().padStart(2, '0');
  const m = d.getMinutes().toString().padStart(2, '0');
  return `${h}:${m} 기준`;
}

function TrendingRow({ item }: { item: TrendingKeyword }) {
  const handleClick = () => {
    safeOpenUrl(`https://search.naver.com/search.naver?query=${encodeURIComponent(item.keyword)}`);
  };

  return (
    <li className={styles.row} onClick={handleClick} role="button">
      <span className={styles.rank}>{item.rank}</span>
      <span className={styles.keyword}>{item.keyword}</span>
      <ChangeIndicator change={item.change} />
    </li>
  );
}

function SkeletonRows({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <li key={i} className={styles.skeletonRow}>
          <span className={styles.skeletonRank} />
          <span className={styles.skeletonKeyword} />
        </li>
      ))}
    </>
  );
}

export function TrendingSection() {
  const [keywords, setKeywords] = useState<TrendingKeyword[]>([]);
  const [updatedAt, setUpdatedAt] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetchTrendingKeywords()
      .then((data) => {
        if (cancelled) return;
        setKeywords(data);
        setUpdatedAt(formatUpdateTime(new Date().toISOString()));
      })
      .catch(() => {
        // 실패 시 빈 상태 유지 (섹션 자체를 숨기지 않음)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const left = keywords.slice(0, 5);
  const right = keywords.slice(5, 10);

  return (
    <div className={styles.section}>
      <div className={styles.sectionHeader}>
        <span className={styles.sectionTitle}>실시간 검색어</span>
        {updatedAt && <span className={styles.updateTime}>{updatedAt}</span>}
      </div>
      <div className={styles.grid}>
        <ol className={styles.column}>
          {isLoading ? (
            <SkeletonRows count={5} />
          ) : left.length === 0 ? (
            <li className={styles.empty}>불러오기 실패</li>
          ) : (
            left.map((item) => <TrendingRow key={item.rank} item={item} />)
          )}
        </ol>
        <ol className={styles.column}>
          {isLoading ? (
            <SkeletonRows count={5} />
          ) : (
            right.map((item) => <TrendingRow key={item.rank} item={item} />)
          )}
        </ol>
      </div>
    </div>
  );
}
