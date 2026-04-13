import { useProfile } from '../hooks/useProfile';
import type { PointTransaction } from '../types/user';
import styles from './ProfilePage.module.css';

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function getReasonLabel(reason: PointTransaction['reason']): string {
  switch (reason) {
    case 'vote': return '투표 참여';
    case 'ad': return '광고 시청';
    case 'share': return '친구 공유';
    default: return '보상';
  }
}

export default function ProfilePage() {
  const { user, transactions, isLoading } = useProfile();

  return (
    <div className={styles.page}>
      {/* 헤더 */}
      <header className={styles.header}>
        <h1 className={styles.headerTitle}>내 정보</h1>
      </header>

      <div className={styles.scrollArea}>
        {/* 포인트 요약 카드 */}
        <div className={styles.pointCard}>
          <div className={styles.pointLabel}>총 적립 포인트</div>
          {isLoading ? (
            <div className={styles.pointSkeleton} />
          ) : (
            <div className={styles.pointAmount}>
              {(user?.totalPoints ?? 0).toLocaleString()}
              <span className={styles.unit}>P</span>
            </div>
          )}
          <div className={styles.todayEarned}>
            오늘 +{user?.todayEarned ?? 0}P 획득
          </div>
        </div>

        {/* 도파민 패스 */}
        <div className={styles.section}>
          <div className={styles.sectionRow}>
            <div>
              <p className={styles.passTitle}>도파민 패스</p>
              <p className={styles.passDesc}>
                {user?.isPremium ? '구독 중 🎉' : '미가입 — 2배 포인트, 광고 제거'}
              </p>
            </div>
            {!user?.isPremium && (
              <button className={styles.subscribeBtn}>구독하기</button>
            )}
          </div>
        </div>

        {/* 포인트 내역 */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>포인트 내역</h2>
          {isLoading ? (
            <div className={styles.historySkeletonWrap}>
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className={styles.historySkeleton} />
              ))}
            </div>
          ) : transactions.length === 0 ? (
            <p className={styles.emptyText}>아직 포인트 내역이 없어요</p>
          ) : (
            <ul className={styles.historyList}>
              {transactions.map((tx) => (
                <li key={tx.id} className={styles.historyItem}>
                  <div className={styles.historyLeft}>
                    <span className={styles.historyReason}>
                      {getReasonLabel(tx.reason)}
                    </span>
                    <span className={styles.historyDate}>
                      {formatDate(tx.createdAt)}
                    </span>
                  </div>
                  <span className={styles.historyAmount}>+{tx.amount}P</span>
                </li>
              ))}
            </ul>
          )}
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
