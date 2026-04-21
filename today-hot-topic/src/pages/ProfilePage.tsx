import { useCallback } from 'react';
import { useProfile } from '../hooks/useProfile';
import { useIAP } from '../hooks/useIAP';
import styles from './ProfilePage.module.css';

export default function ProfilePage() {
  const { user, isLoading, refetch } = useProfile();

  const onPremiumActivated = useCallback(() => {
    refetch();
  }, [refetch]);

  const { status: iapStatus, price, isSupported, purchase } = useIAP(onPremiumActivated);

  const isPremium = user?.isPremium ?? false;
  const isPurchasing = iapStatus === 'loading';

  return (
    <div className={styles.page}>
      {/* 헤더 */}
      <header className={styles.header}>
        <h1 className={styles.headerTitle}>내 정보</h1>
      </header>

      <div className={styles.scrollArea}>
        {/* 도파민 패스 */}
        <div className={styles.section}>
          <div className={styles.sectionRow}>
            <div>
              <p className={styles.passTitle}>도파민 패스</p>
              <p className={styles.passDesc}>
                {isLoading
                  ? '...'
                  : isPremium
                  ? '구독 중 🎉 — 광고 없이 즐기는 중'
                  : `광고 없이 핫이슈를 즐겨요${price ? ` · ${price}` : ''}`}
              </p>
            </div>
            {!isLoading && !isPremium && (
              <button
                className={styles.subscribeBtn}
                onClick={purchase}
                disabled={isPurchasing || !isSupported}
              >
                {isPurchasing ? '결제 중...' : '구독하기'}
              </button>
            )}
          </div>
        </div>

        {/* 알림 설정 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>알림 설정</h2>
          <div className={styles.sectionRow}>
            <span className={styles.toggleLabel}>핫토픽 알림</span>
            <label className={styles.toggle}>
              <input type="checkbox" defaultChecked />
              <span className={styles.toggleSlider} />
            </label>
          </div>
        </div>

        <div style={{ height: 32 }} />
      </div>
    </div>
  );
}
