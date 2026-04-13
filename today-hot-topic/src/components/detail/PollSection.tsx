import { motion, AnimatePresence } from 'framer-motion';
import { generateHapticFeedback } from '@apps-in-toss/web-framework';
import type { Poll } from '../../types/topic';
import { VoteResultBar } from './VoteResultBar';
import styles from './PollSection.module.css';

interface PollSectionProps {
  poll: Poll;
  hasVoted: boolean;
  votedOption: 'A' | 'B' | null;
  onVote: (option: 'A' | 'B') => void;
  isSubmitting: boolean;
}

export function PollSection({
  poll,
  hasVoted,
  votedOption,
  onVote,
  isSubmitting,
}: PollSectionProps) {
  const handleVote = (option: 'A' | 'B') => {
    if (hasVoted || isSubmitting) return;
    generateHapticFeedback({ type: 'softMedium' });
    onVote(option);
  };

  return (
    <div className={styles.section}>
      <h3 className={styles.question}>너의 생각은?</h3>

      <AnimatePresence mode="wait">
        {!hasVoted ? (
          <motion.div
            key="buttons"
            className={styles.buttons}
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            <button
              className={styles.optionBtn}
              onClick={() => handleVote('A')}
              disabled={isSubmitting}
            >
              <span className={styles.optionLabel}>A</span>
              <span className={styles.optionText}>{poll.optionAText}</span>
            </button>
            <button
              className={styles.optionBtn}
              onClick={() => handleVote('B')}
              disabled={isSubmitting}
            >
              <span className={styles.optionLabel}>B</span>
              <span className={styles.optionText}>{poll.optionBText}</span>
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <VoteResultBar
              optionAText={poll.optionAText}
              optionBText={poll.optionBText}
              optionACount={poll.optionACount}
              optionBCount={poll.optionBCount}
              votedOption={votedOption}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {isSubmitting && (
        <div className={styles.submitting}>
          <div className={styles.spinner} />
        </div>
      )}
    </div>
  );
}
