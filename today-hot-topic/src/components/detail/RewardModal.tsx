import { motion, AnimatePresence } from 'framer-motion';
import styles from './RewardModal.module.css';

interface RewardModalProps {
  isOpen: boolean;
  onClose: () => void;
  amount: number;
  balance: number;
}

export function RewardModal({ isOpen, onClose, amount, balance }: RewardModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 오버레이 */}
          <motion.div
            className={styles.overlay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />

          {/* 모달 */}
          <motion.div
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.85, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
          >
            {/* 포인트 애니메이션 */}
            <motion.div
              className={styles.pointBadge}
              initial={{ scale: 0, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', damping: 12, stiffness: 200, delay: 0.1 }}
            >
              <span className={styles.confetti}>🎉</span>
              <motion.span
                className={styles.pointAmount}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 }}
              >
                +{amount}P
              </motion.span>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h2 className={styles.title}>투표 참여 보상이</h2>
              <h2 className={styles.title}>지급되었어요</h2>
            </motion.div>

            <motion.div
              className={styles.balanceBox}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <span className={styles.balanceLabel}>현재 잔액</span>
              <span className={styles.balanceAmount}>
                {balance.toLocaleString()}P
              </span>
            </motion.div>

            <motion.div
              className={styles.actions}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
            >
              <button className={styles.confirmBtn} onClick={onClose}>
                확인
              </button>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
