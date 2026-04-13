import { lazy, Suspense } from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { useDeviceViewport } from './hooks/useDeviceViewport';
import { useAuth } from './hooks/useAuth';
import { BottomNav } from './components/layout/BottomNav';
import HomePage from './pages/HomePage';
import DetailPage from './pages/DetailPage';
import ProfilePage from './pages/ProfilePage';
import styles from './App.module.css';

const pageVariants = {
  initial: { x: '100%', opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: '-30%', opacity: 0 },
};

const pageTransition = {
  duration: 0.25,
  ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number],
};

function AnimatedRoutes() {
  const location = useLocation();
  const isDetailPage = location.pathname.startsWith('/topics/');

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={isDetailPage ? pageVariants : undefined}
        initial={isDetailPage ? 'initial' : false}
        animate={isDetailPage ? 'animate' : undefined}
        exit={isDetailPage ? 'exit' : undefined}
        transition={pageTransition}
        className={styles.pageWrapper}
      >
        <Routes location={location}>
          <Route path="/" element={<HomePage />} />
          <Route path="/topics/:id" element={<DetailPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

function AppInner() {
  useDeviceViewport();
  // Mock 모드가 아닐 때만 실제 Toss 로그인 실행
  const { isLoading: authLoading } = useAuth();
  const location = useLocation();
  const isDetailPage = location.pathname.startsWith('/topics/');

  if (authLoading && import.meta.env.PUBLIC_USE_MOCK !== 'true') {
    return <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center' }} />;
  }

  return (
    <div className={styles.appShell}>
      <div className={styles.content}>
        <AnimatedRoutes />
      </div>
      {!isDetailPage && <BottomNav />}
    </div>
  );
}

const IS_MOCK = import.meta.env.PUBLIC_USE_MOCK === 'true';

function PassThrough({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

// mock 모드에서는 @toss/tds-mobile-ait를 번들에서 완전히 제외
// (해당 패키지는 Toss 앱 환경에서만 동작하며, 일반 브라우저에서 모듈 초기화 시 throw)
const TDSProvider = IS_MOCK
  ? PassThrough
  : lazy(() =>
      import('@toss/tds-mobile-ait').then((m) => ({ default: m.TDSMobileAITProvider }))
    );

export default function App() {
  return (
    <Suspense fallback={null}>
      <TDSProvider>
        <HashRouter>
          <AppInner />
        </HashRouter>
      </TDSProvider>
    </Suspense>
  );
}
