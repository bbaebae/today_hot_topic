import type { Category } from '../../types/topic';
import styles from './CategoryTab.module.css';
import clsx from 'clsx';
import { safeHaptic } from '../../utils/toss';

const CATEGORIES: { key: Category; label: string }[] = [
  { key: 'story', label: '썰' },
  { key: 'news', label: '뉴스' },
  { key: 'finance', label: '금융' },
];

interface CategoryTabProps {
  selected: Category;
  onChange: (category: Category) => void;
}

export function CategoryTab({ selected, onChange }: CategoryTabProps) {
  const handleChange = (cat: Category) => {
    if (cat === selected) return;
    safeHaptic({ type: 'softMedium' });
    onChange(cat);
  };

  return (
    <div className={styles.tabBar}>
      {CATEGORIES.map(({ key, label }) => (
        <button
          key={key}
          className={clsx(styles.tabItem, selected === key && styles.active)}
          onClick={() => handleChange(key)}
        >
          {label}
          {selected === key && <span className={styles.indicator} />}
        </button>
      ))}
    </div>
  );
}
