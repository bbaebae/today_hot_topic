import { motion } from 'framer-motion';
import styles from './VoteResultBar.module.css';
import clsx from 'clsx';

interface VoteResultBarProps {
  optionAText: string;
  optionBText: string;
  optionACount: number;
  optionBCount: number;
  votedOption: 'A' | 'B' | null;
}

export function VoteResultBar({
  optionAText,
  optionBText,
  optionACount,
  optionBCount,
  votedOption,
}: VoteResultBarProps) {
  const total = optionACount + optionBCount;
  const pctA = total === 0 ? 50 : Math.round((optionACount / total) * 100);
  const pctB = 100 - pctA;
  const totalStr = total.toLocaleString();

  return (
    <div className={styles.resultWrap}>
      <div className={styles.bar}>
        <motion.div
          className={clsx(styles.barA, votedOption === 'A' && styles.voted)}
          initial={{ flex: 0 }}
          animate={{ flex: pctA }}
          transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          {pctA >= 20 && (
            <span className={styles.pctLabel}>{pctA}%</span>
          )}
        </motion.div>
        <motion.div
          className={clsx(styles.barB, votedOption === 'B' && styles.voted)}
          initial={{ flex: 0 }}
          animate={{ flex: pctB }}
          transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          {pctB >= 20 && (
            <span className={styles.pctLabel}>{pctB}%</span>
          )}
        </motion.div>
      </div>

      <div className={styles.labels}>
        <div className={clsx(styles.optionLabel, votedOption === 'A' && styles.myVote)}>
          {votedOption === 'A' && <span className={styles.checkIcon}>✓ </span>}
          {optionAText}
        </div>
        <div className={clsx(styles.optionLabel, styles.right, votedOption === 'B' && styles.myVote)}>
          {optionBText}
          {votedOption === 'B' && <span className={styles.checkIcon}> ✓</span>}
        </div>
      </div>

      <p className={styles.totalCount}>총 {totalStr}명 참여</p>
    </div>
  );
}
