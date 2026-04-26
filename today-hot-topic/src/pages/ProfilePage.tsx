import { useRef, useEffect, useState } from 'react';
import { TossAds } from '@apps-in-toss/web-framework';
import { useProfile } from '../hooks/useProfile';
import { convertToTossPoints } from '../services/userService';
import styles from './ProfilePage.module.css';

const PROFILE_FEED_AD_GROUP_ID =
  import.meta.env.VITE_PROFILE_FEED_AD_GROUP_ID ?? 'ait.v2.live.32cd1e159b6b4a08';

function ProfileFeedAd() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (!PROFILE_FEED_AD_GROUP_ID) { setVisible(false); return; }
    try {
      if (!TossAds.attachBanner.isSupported() || !containerRef.current) { setVisible(false); return; }
      const attached = TossAds.attachBanner(PROFILE_FEED_AD_GROUP_ID, containerRef.current, {
        tone: 'grey',
        variant: 'expanded',
        theme: 'light',
        callbacks: {
          onNoFill: () => setVisible(false),
          onAdFailedToRender: () => setVisible(false),
        },
      });
      return () => attached?.destroy();
    } catch {
      setVisible(false);
    }
  }, []);

  if (!visible) return null;

  return (
    <div className={styles.feedAdWrapper}>
      <div ref={containerRef} style={{ width: '100%' }} />
    </div>
  );
}

export default function ProfilePage() {
  const { user, isLoading, refetch } = useProfile();
  const [isConverting, setIsConverting] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  const totalPoints = user?.totalPoints ?? 0;

  const showToast = (msg: string, type: 'success' | 'error') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 2500);
  };

  const handleConvert = async () => {
    if (isConverting || totalPoints === 0) return;
    setIsConverting(true);
    try {
      const result = await convertToTossPoints(totalPoints);
      await refetch();
      showToast(`${result.converted.toLocaleString()}P → 토스 포인트 전환 완료!`, 'success');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '포인트 변환에 실패했어요.';
      showToast(msg, 'error');
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className={styles.page}>
      {/* 토스트 */}
      {toast && (
        <div className={`${styles.toast} ${toast.type === 'error' ? styles.toastError : ''}`}>
          {toast.msg}
        </div>
      )}

      <header className={styles.header}>
        <h1 className={styles.headerTitle}>내 포인트</h1>
      </header>

      <div className={styles.scrollArea}>
        {/* 포인트 잔액 */}
        <div className={styles.pointCard}>
          <p className={styles.pointLabel}>보유 포인트</p>
          {isLoading ? (
            <div className={styles.pointSkeleton} />
          ) : (
            <p className={styles.pointAmount}>
              {totalPoints.toLocaleString()}<span className={styles.unit}>P</span>
            </p>
          )}
          <p className={styles.todayEarned}>더보기 광고를 보면 포인트가 쌓여요</p>
          <button
            className={styles.convertBtn}
            onClick={handleConvert}
            disabled={isLoading || isConverting || totalPoints === 0}
          >
            {isConverting ? '변환 중...' : '토스 포인트로 전환'}
          </button>
        </div>

        {/* 피드형 광고 */}
        <ProfileFeedAd />

        <div style={{ height: 32 }} />
      </div>
    </div>
  );
}
