import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { safeOpenUrl } from '../utils/toss';
import styles from './WebViewerPage.module.css';

function toMobileUrl(url: string): string {
  try {
    const u = new URL(url);
    const host = u.hostname;
    // 이미 모바일 서브도메인
    if (host.startsWith('m.') || host.startsWith('mobile.')) return url;
    // 모바일 서브도메인 없는 사이트 (변환 스킵)
    if (host.includes('bobaedream.co.kr') || host.includes('naver.com') || host.includes('coindesk')) return url;
    // news. 서브도메인은 이미 최적화된 경우 (news.jtbc.co.kr 등)
    if (host.startsWith('news.')) return url;
    // 중앙일보 특수 케이스
    if (host.includes('joins.com') || host.includes('joongang')) {
      u.hostname = 'mnews.joins.com';
      return u.toString();
    }
    // www. → m. 치환
    if (host.startsWith('www.')) {
      u.hostname = 'm.' + host.slice(4);
      return u.toString();
    }
    // 그 외: m. 추가 (fmkorea.com → m.fmkorea.com, pann.nate.com → m.pann.nate.com)
    u.hostname = 'm.' + host;
    return u.toString();
  } catch {
    return url;
  }
}

export default function WebViewerPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const rawUrl = params.get('url') ?? '';
  const url = rawUrl ? toMobileUrl(rawUrl) : '';
  const [loadError, setLoadError] = useState(false);

  if (!url) {
    navigate(-1);
    return null;
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button className={styles.backBtn} onClick={() => navigate(-1)} aria-label="뒤로">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <span className={styles.headerUrl}>{new URL(url).hostname.replace('www.', '')}</span>
        <button className={styles.externalBtn} onClick={() => safeOpenUrl(url)} aria-label="외부 브라우저로 열기">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <polyline points="15 3 21 3 21 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="10" y1="14" x2="21" y2="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </header>

      {loadError ? (
        <div className={styles.errorArea}>
          <p className={styles.errorText}>이 페이지는 앱 내에서 열 수 없어요.</p>
          <button className={styles.openExternalBtn} onClick={() => safeOpenUrl(url)}>
            브라우저에서 열기
          </button>
        </div>
      ) : (
        <iframe
          className={styles.frame}
          src={url}
          title="원본 기사"
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
          onError={() => setLoadError(true)}
        />
      )}
    </div>
  );
}
