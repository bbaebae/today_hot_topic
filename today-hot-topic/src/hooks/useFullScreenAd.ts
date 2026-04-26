import { useState, useEffect, useCallback, useRef } from 'react';
import { loadFullScreenAd, showFullScreenAd } from '@apps-in-toss/web-framework';

const AD_GROUP_ID =
  import.meta.env.VITE_INTERSTITIAL_AD_GROUP_ID ?? 'ait.v2.live.6eca1c2eb37644af';

// 최소 N번 클릭 후부터 광고 노출 대상
const MIN_CLICKS_BEFORE_AD = 3;
// 노출 대상이 된 후 광고를 실제로 보여줄 확률 (0~1)
const AD_PROBABILITY = 0.4;

const SS_CLICK_COUNT = 'ad_click_count';

function isFnSupported(fn: { isSupported?: () => boolean }): boolean {
  try {
    return fn.isSupported?.() ?? false;
  } catch {
    return false;
  }
}

export function useFullScreenAd() {
  const [isLoaded, setIsLoaded] = useState(false);
  const unregisterRef = useRef<(() => void) | null>(null);
  const clickCountRef = useRef(parseInt(sessionStorage.getItem(SS_CLICK_COUNT) ?? '0', 10));

  const loadAd = useCallback(() => {
    if (!isFnSupported(loadFullScreenAd)) return;
    setIsLoaded(false);

    const unregister = loadFullScreenAd({
      options: { adGroupId: AD_GROUP_ID },
      onEvent: (event) => {
        if (event.type === 'loaded') setIsLoaded(true);
      },
      onError: (error) => {
        console.error('[Ad] 로드 실패:', error);
      },
    });

    unregisterRef.current = unregister;
  }, []);

  // 마운트 시 미리 로드
  useEffect(() => {
    loadAd();
    return () => {
      unregisterRef.current?.();
    };
  }, [loadAd]);

  /**
   * 클릭마다 호출. 조건 충족 시 광고 노출 후 onNavigate 실행.
   * @param onNavigate 광고 종료(또는 스킵) 후 실행할 콜백
   * @param skip true면 광고 없이 즉시 실행 (프리미엄 유저)
   */
  const maybeShow = useCallback(
    (onNavigate: () => void, skip = false) => {
      clickCountRef.current += 1;
      sessionStorage.setItem(SS_CLICK_COUNT, String(clickCountRef.current));

      const shouldShow =
        !skip &&
        isFnSupported(showFullScreenAd) &&
        isLoaded &&
        clickCountRef.current >= MIN_CLICKS_BEFORE_AD &&
        Math.random() < AD_PROBABILITY;

      if (!shouldShow) {
        onNavigate();
        return;
      }

      // 광고 노출 → 카운터 리셋
      clickCountRef.current = 0;
      sessionStorage.setItem(SS_CLICK_COUNT, '0');

      showFullScreenAd({
        options: { adGroupId: AD_GROUP_ID },
        onEvent: (event) => {
          if (event.type === 'dismissed' || event.type === 'failedToShow') {
            loadAd();
            onNavigate();
          }
        },
        onError: (error) => {
          console.error('[Ad] 표시 실패:', error);
          loadAd();
          onNavigate();
        },
      });
    },
    [isLoaded, loadAd],
  );

  return { isLoaded, maybeShow };
}
