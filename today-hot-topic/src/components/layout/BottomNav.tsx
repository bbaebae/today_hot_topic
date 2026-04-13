import { useNavigate, useLocation } from 'react-router-dom';
import { generateHapticFeedback } from '@apps-in-toss/web-framework';
import styles from './BottomNav.module.css';
import clsx from 'clsx';

const navItems = [
  {
    path: '/',
    label: '홈',
    icon: (active: boolean) => (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path
          d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"
          stroke={active ? 'var(--color-blue-500)' : 'var(--color-gray-400)'}
          strokeWidth="2"
          fill={active ? 'var(--color-blue-50)' : 'none'}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <polyline
          points="9 22 9 12 15 12 15 22"
          stroke={active ? 'var(--color-blue-500)' : 'var(--color-gray-400)'}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    path: '/profile',
    label: '내 포인트',
    icon: (active: boolean) => (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <circle
          cx="12"
          cy="8"
          r="4"
          stroke={active ? 'var(--color-blue-500)' : 'var(--color-gray-400)'}
          strokeWidth="2"
        />
        <path
          d="M4 20c0-4 3.58-7 8-7s8 3 8 7"
          stroke={active ? 'var(--color-blue-500)' : 'var(--color-gray-400)'}
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    ),
  },
];

export function BottomNav() {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const handleNav = (path: string) => {
    if (pathname === path) return;
    generateHapticFeedback({ type: 'softMedium' });
    navigate(path);
  };

  return (
    <nav className={styles.bottomNav}>
      {navItems.map((item) => {
        const isActive = pathname === item.path;
        return (
          <button
            key={item.path}
            className={clsx(styles.navItem, isActive && styles.active)}
            onClick={() => handleNav(item.path)}
          >
            {item.icon(isActive)}
            <span className={styles.label}>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
