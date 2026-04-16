import { motion } from 'framer-motion';
import { safeOpenUrl } from '../../utils/toss';
import styles from './SummaryCard.module.css';

interface SummaryCardProps {
  summaries: string[];
  sourceUrl: string;
  sourceName?: string;
  createdAt: string;
}

function formatTimeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (diff < 1) return '방금 전';
  if (diff < 60) return `${diff}분 전`;
  const hours = Math.floor(diff / 60);
  if (hours < 24) return `${hours}시간 전`;
  return `${Math.floor(hours / 24)}일 전`;
}

function getSourceName(url: string): string {
  if (url.includes('nate.com')) return '네이트판';
  if (url.includes('ruliweb.com')) return '루리웹';
  if (url.includes('dcinside')) return '디시인사이드';
  if (url.includes('fmkorea')) return '펨코';
  if (url.includes('naver.com')) return '네이버';
  if (url.includes('coindesk')) return '코인데스크';
  return '커뮤니티';
}

export function SummaryCard({
  summaries,
  sourceUrl,
  createdAt,
}: SummaryCardProps) {
  return (
    <motion.div
      className={styles.card}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
    >
      <div className={styles.header}>
        <div className={styles.aiLabel}>
          <span className={styles.aiIcon}>✨</span>
          <span>AI 3줄 요약</span>
        </div>
        <div className={styles.source}>
          <span>{getSourceName(sourceUrl)}</span>
          <span className={styles.dot}>·</span>
          <span>{formatTimeAgo(createdAt)}</span>
        </div>
      </div>

      <ol className={styles.summaryList}>
        {summaries.map((line, i) => (
          <motion.li
            key={i}
            className={styles.summaryItem}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.15 + i * 0.08 }}
          >
            <span className={styles.number}>{i + 1}</span>
            <span className={styles.text}>{line}</span>
          </motion.li>
        ))}
      </ol>

      {sourceUrl && (
        <button
          className={styles.sourceBtn}
          onClick={() => safeOpenUrl(sourceUrl)}
        >
          원본 보기 →
        </button>
      )}
    </motion.div>
  );
}
