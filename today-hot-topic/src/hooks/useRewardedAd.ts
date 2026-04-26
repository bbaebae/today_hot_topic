import { useState, useEffect, useCallback, useRef } from 'react';
import { loadFullScreenAd, showFullScreenAd } from '@apps-in-toss/web-framework';
import { recordAdWatched } from '../services/userService';

const REWARDED_AD_GROUP_ID =
  import.meta.env.VITE_REWARDED_AD_GROUP_ID ?? 'ait.v2.live.5b162386051140c1';

function isFnSupported(fn: { isSupported?: () => boolean }): boolean {
  try {
    return fn.isSupported?.() ?? false;
  } catch {
    return false;
  }
}

export function useRewardedAd(onPointsEarned?: (points: number) => void) {
  const [isLoaded, setIsLoaded] = useState(false);
  const unregisterRef = useRef<(() => void) | null>(null);

  const loadAd = useCallback(() => {
    if (!isFnSupported(loadFullScreenAd)) return;
    setIsLoaded(false);

    const unregister = loadFullScreenAd({
      options: { adGroupId: REWARDED_AD_GROUP_ID },
      onEvent: (event) => {
        if (event.type === 'loaded') setIsLoaded(true);
      },
      onError: () => {},
    });

    unregisterRef.current = unregister;
  }, []);

  useEffect(() => {
    loadAd();
    return () => {
      unregisterRef.current?.();
    };
  }, [loadAd]);

  /**
   * 리워드 광고를 보여줍니다.
   * @param onComplete 광고 완료(보상 지급 후) 또는 스킵 시 실행할 콜백
   */
  const showAd = useCallback(
    (onComplete: () => void) => {
      if (!isFnSupported(showFullScreenAd) || !isLoaded) {
        // 광고 미지원/미로드 시 즉시 완료
        onComplete();
        return;
      }

      let rewarded = false;

      showFullScreenAd({
        options: { adGroupId: REWARDED_AD_GROUP_ID },
        onEvent: async (event) => {
          if (event.type === 'userEarnedReward') {
            rewarded = true;
            try {
              const result = await recordAdWatched();
              onPointsEarned?.(result.earned);
            } catch {
              // 포인트 적립 실패해도 더보기는 진행
            }
          }
          if (event.type === 'dismissed' || event.type === 'failedToShow') {
            loadAd();
            // 보상 없이 닫으면(스킵 등)도 더보기는 진행
            if (!rewarded) onComplete();
            else onComplete();
          }
        },
        onError: () => {
          loadAd();
          onComplete();
        },
      });
    },
    [isLoaded, loadAd, onPointsEarned],
  );

  return { isLoaded, showAd };
}
