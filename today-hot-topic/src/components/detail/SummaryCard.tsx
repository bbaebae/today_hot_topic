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
  // 언론사
  if (url.includes('chosun.com')) return '조선일보';
  if (url.includes('donga.com')) return '동아일보';
  if (url.includes('hani.co.kr')) return '한겨레';
  if (url.includes('khan.co.kr')) return '경향신문';
  if (url.includes('newsis.com')) return '뉴시스';
  if (url.includes('seoul.co.kr')) return '서울신문';
  if (url.includes('segye.com')) return '세계일보';
  if (url.includes('newscj.com')) return '천지일보';
  if (url.includes('yonhapnews') || url.includes('yna.co.kr')) return '연합뉴스';
  if (url.includes('jtbc.co.kr')) return 'JTBC';
  if (url.includes('mbc.co.kr')) return 'MBC';
  if (url.includes('kbs.co.kr')) return 'KBS';
  if (url.includes('sbs.co.kr')) return 'SBS';
  if (url.includes('joins.com') || url.includes('joongang')) return '중앙일보';
  if (url.includes('hankyung.com')) return '한국경제';
  if (url.includes('mk.co.kr')) return '매일경제';
  if (url.includes('edaily.co.kr')) return '이데일리';
  // 커뮤니티
  if (url.includes('nate.com')) return '네이트판';
  if (url.includes('theqoo.net')) return '더쿠';
  if (url.includes('instiz.net')) return '인스티즈';
  if (url.includes('ruliweb.com')) return '루리웹';
  if (url.includes('dcinside')) return '디시인사이드';
  if (url.includes('fmkorea')) return '펨코';
  if (url.includes('todayhumor')) return '오늘의유머';
  if (url.includes('bobaedream')) return '보배드림';
  if (url.includes('mlbpark')) return 'MLB파크';
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
