import type { Topic } from '../../types/topic';
import { safeHaptic } from '../../utils/toss';
import styles from './TopicItem.module.css';
import clsx from 'clsx';

interface TopicItemProps {
  topic: Topic;
  onClick: () => void;
}

function formatViewCount(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}만`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}천`;
  return String(n);
}

function formatTimeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (diff < 1) return '방금 전';
  if (diff < 60) return `${diff}분 전`;
  const hours = Math.floor(diff / 60);
  if (hours < 24) return `${hours}시간 전`;
  return `${Math.floor(hours / 24)}일 전`;
}

export function TopicItem({ topic, onClick }: TopicItemProps) {
  const isHot = topic.rank <= 3;

  const handleClick = () => {
    safeHaptic({ type: 'softMedium' });
    onClick();
  };

  return (
    <li className={styles.item} onClick={handleClick}>
      <div className={clsx(styles.rank, isHot && styles.hot)}>
        {isHot ? '🔥' : topic.rank}
      </div>

      <div className={styles.content}>
        <p className={styles.title}>{topic.title}</p>
        <div className={styles.meta}>
          <span>조회 {formatViewCount(topic.viewCount)}</span>
          <span className={styles.dot}>·</span>
          <span>{formatTimeAgo(topic.createdAt)}</span>
        </div>
      </div>

      {topic.imageUrl && (
        <div className={styles.thumbnail}>
          <img src={topic.imageUrl} alt="" loading="lazy" />
        </div>
      )}

      <div className={styles.chevron}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path
            d="M9 18l6-6-6-6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </li>
  );
}
