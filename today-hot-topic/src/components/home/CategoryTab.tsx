import type { MainTab } from '../../types/topic';
import styles from './CategoryTab.module.css';
import clsx from 'clsx';
import { safeHaptic } from '../../utils/toss';

const MAIN_TABS: { key: MainTab; label: string }[] = [
  { key: 'story', label: '썰' },
  { key: 'news', label: '뉴스' },
];

interface CategoryTabProps {
  selected: MainTab;
  onChange: (tab: MainTab) => void;
}

export function CategoryTab({ selected, onChange }: CategoryTabProps) {
  const handleChange = (tab: MainTab) => {
    if (tab === selected) return;
    safeHaptic({ type: 'softMedium' });
    onChange(tab);
  };

  return (
    <div className={styles.tabBar}>
      {MAIN_TABS.map(({ key, label }) => (
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
