import { motion, AnimatePresence } from 'framer-motion';
import styles from './AdConfirmModal.module.css';

interface AdConfirmModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function AdConfirmModal({ isOpen, onConfirm, onCancel }: AdConfirmModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className={styles.overlay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onCancel}
          />

          <motion.div
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.85, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
          >
            <span className={styles.icon}>🎁</span>

            <div className={styles.textWrap}>
              <h2 className={styles.title}>광고를 보고</h2>
              <h2 className={styles.title}>포인트를 받을까요?</h2>
              <p className={styles.desc}>짧은 광고 시청 후 포인트가 지급돼요</p>
            </div>

            <div className={styles.actions}>
              <button className={styles.confirmBtn} onClick={onConfirm}>
                예, 볼게요
              </button>
              <button className={styles.cancelBtn} onClick={onCancel}>
                아니요
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
