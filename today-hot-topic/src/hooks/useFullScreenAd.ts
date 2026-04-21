import { useState, useEffect, useCallback, useRef } from 'react';
import { loadFullScreenAd, showFullScreenAd } from '@apps-in-toss/web-framework';

const AD_GROUP_ID =
  import.meta.env.VITE_INTERSTITIAL_AD_GROUP_ID ?? 'ait.dev.43daa14da3ae487b';

export function useFullScreenAd() {
  const [isLoaded, setIsLoaded] = useState(false);
  const unregisterRef = useRef<(() => void) | null>(null);

  const loadAd = useCallback(() => {
    if (!loadFullScreenAd.isSupported()) return;
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
   * 광고를 표시합니다.
   * @param onDismissed 광고가 닫히거나 지원되지 않을 때 실행할 콜백
   * @param skip true면 광고 없이 onDismissed 즉시 실행 (프리미엄 유저)
   */
  const show = useCallback(
    (onDismissed: () => void, skip = false) => {
      if (skip || !showFullScreenAd.isSupported() || !isLoaded) {
        onDismissed();
        return;
      }

      showFullScreenAd({
        options: { adGroupId: AD_GROUP_ID },
        onEvent: (event) => {
          if (event.type === 'dismissed' || event.type === 'failedToShow') {
            loadAd(); // 다음 광고 미리 로드
            onDismissed();
          }
        },
        onError: (error) => {
          console.error('[Ad] 표시 실패:', error);
          loadAd();
          onDismissed();
        },
      });
    },
    [isLoaded, loadAd],
  );

  return { isLoaded, show };
}
