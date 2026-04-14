import type { NewsSubCategory } from '../../types/topic';
import styles from './NewsSubTab.module.css';
import clsx from 'clsx';
import { safeHaptic } from '../../utils/toss';

const NEWS_SUBS: { key: NewsSubCategory; label: string }[] = [
  { key: 'society', label: '사회' },
  { key: 'economy', label: '경제' },
  { key: 'sports', label: '스포츠' },
  { key: 'love', label: '연애' },
];

interface NewsSubTabProps {
  selected: NewsSubCategory;
  onChange: (sub: NewsSubCategory) => void;
}

export function NewsSubTab({ selected, onChange }: NewsSubTabProps) {
  const handleChange = (sub: NewsSubCategory) => {
    if (sub === selected) return;
    safeHaptic({ type: 'softMedium' });
    onChange(sub);
  };

  return (
    <div className={styles.subTabBar}>
      {NEWS_SUBS.map(({ key, label }) => (
        <button
          key={key}
          className={clsx(styles.subTabItem, selected === key && styles.active)}
          onClick={() => handleChange(key)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
