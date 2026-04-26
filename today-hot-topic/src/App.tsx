import { lazy, Suspense, useEffect } from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { TossAds } from '@apps-in-toss/web-framework';
import { useDeviceViewport } from './hooks/useDeviceViewport';
import { useAuth } from './hooks/useAuth';
import { BottomNav } from './components/layout/BottomNav';
import HomePage from './pages/HomePage';
import DetailPage from './pages/DetailPage';
import ProfilePage from './pages/ProfilePage';
import WebViewerPage from './pages/WebViewerPage';
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
  const isViewerPage = location.pathname === '/viewer';

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={isDetailPage || isViewerPage ? pageVariants : undefined}
        initial={isDetailPage || isViewerPage ? 'initial' : false}
        animate={isDetailPage || isViewerPage ? 'animate' : undefined}
        exit={isDetailPage || isViewerPage ? 'exit' : undefined}
        transition={pageTransition}
        className={styles.pageWrapper}
      >
        <Routes location={location}>
          <Route path="/" element={<HomePage />} />
          <Route path="/topics/:id" element={<DetailPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/viewer" element={<WebViewerPage />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

function AppInner() {
  useDeviceViewport();
  const { isLoading: authLoading } = useAuth();

  useEffect(() => {
    try {
      if (!TossAds.initialize.isSupported()) return;
      TossAds.initialize({
        callbacks: {
          onInitializationFailed: (error) => console.error('[TossAds] init failed:', error),
        },
      });
    } catch {
      // not in Toss app environment
    }
  }, []);
  const location = useLocation();
  const isDetailPage = location.pathname.startsWith('/topics/');
  const isViewerPage = location.pathname === '/viewer';

  if (authLoading) {
    return <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center' }} />;
  }

  return (
    <div className={styles.appShell}>
      <div className={styles.content}>
        <AnimatedRoutes />
      </div>
      {!isDetailPage && !isViewerPage && <BottomNav />}
    </div>
  );
}

const IS_MOCK = import.meta.env.PUBLIC_USE_MOCK === 'true';
// ReactNativeWebView가 있으면 토스 앱 WebView 환경
const IS_TOSS_APP = typeof window !== 'undefined' && 'ReactNativeWebView' in window;

function PassThrough({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

// 토스 앱 WebView 환경에서만 TDSProvider 로드 (일반 브라우저에서 throw 방지)
const TDSProvider = IS_MOCK || !IS_TOSS_APP
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
