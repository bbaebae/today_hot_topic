import { mockTrendingKeywords } from '../../mocks/trending';
import type { TrendingKeyword } from '../../types/topic';
import styles from './TrendingSection.module.css';

function ChangeIndicator({ change }: { change: TrendingKeyword['change'] }) {
  if (change === 'new') return <span className={styles.badgeNew}>NEW</span>;
  if (change === 'up') return <span className={styles.arrowUp}>▲</span>;
  if (change === 'down') return <span className={styles.arrowDown}>▼</span>;
  return <span className={styles.arrowSame}>–</span>;
}

function getUpdateTime() {
  const now = new Date();
  const h = now.getHours().toString().padStart(2, '0');
  const m = now.getMinutes().toString().padStart(2, '0');
  return `${h}:${m} 기준`;
}

export function TrendingSection() {
  const left = mockTrendingKeywords.slice(0, 5);
  const right = mockTrendingKeywords.slice(5, 10);

  return (
    <div className={styles.section}>
      <div className={styles.sectionHeader}>
        <span className={styles.sectionTitle}>실시간 검색어</span>
        <span className={styles.updateTime}>{getUpdateTime()}</span>
      </div>
      <div className={styles.grid}>
        <ol className={styles.column}>
          {left.map((item) => (
            <li key={item.rank} className={styles.row}>
              <span className={styles.rank}>{item.rank}</span>
              <span className={styles.keyword}>{item.keyword}</span>
              <ChangeIndicator change={item.change} />
            </li>
          ))}
        </ol>
        <ol className={styles.column}>
          {right.map((item) => (
            <li key={item.rank} className={styles.row}>
              <span className={styles.rank}>{item.rank}</span>
              <span className={styles.keyword}>{item.keyword}</span>
              <ChangeIndicator change={item.change} />
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
