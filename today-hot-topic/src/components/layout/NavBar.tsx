import { useNavigate } from 'react-router-dom';
import { generateHapticFeedback } from '@apps-in-toss/web-framework';
import styles from './NavBar.module.css';

interface NavBarProps {
  title?: string;
  showBack?: boolean;
  showShare?: boolean;
  onBack?: () => void;
  onShare?: () => void;
}

export function NavBar({
  title,
  showBack = true,
  showShare = false,
  onBack,
  onShare,
}: NavBarProps) {
  const navigate = useNavigate();

  const handleBack = () => {
    generateHapticFeedback({ type: 'softMedium' });
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  const handleShare = () => {
    generateHapticFeedback({ type: 'softMedium' });
    if (onShare) onShare();
  };

  return (
    <header className={styles.navbar}>
      {showBack ? (
        <button className={styles.iconBtn} onClick={handleBack} aria-label="뒤로가기">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M15 18L9 12L15 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      ) : (
        <div className={styles.iconBtn} />
      )}

      {title && <h1 className={styles.title}>{title}</h1>}

      {showShare ? (
        <button className={styles.iconBtn} onClick={handleShare} aria-label="공유">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8M16 6l-4-4-4 4M12 2v13"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      ) : (
        <div className={styles.iconBtn} />
      )}
    </header>
  );
}
