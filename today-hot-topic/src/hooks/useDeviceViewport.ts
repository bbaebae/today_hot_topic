import { useEffect } from 'react';
import { getPlatformOS } from '@apps-in-toss/web-framework';

export function useDeviceViewport() {
  useEffect(() => {
    let isIOS = false;
    try {
      isIOS = getPlatformOS() === 'ios';
    } catch {
      // Toss 앱 환경 밖(일반 브라우저)에서는 네이티브 브리지 없음 → 무시
    }

    document.documentElement.style.setProperty(
      '--min-height',
      `${window.innerHeight}px`
    );

    if (isIOS) {
      document.documentElement.style.setProperty(
        '--bottom-padding',
        'max(env(safe-area-inset-bottom), 20px)'
      );
      document.documentElement.style.setProperty(
        '--top-padding',
        'max(env(safe-area-inset-top), 20px)'
      );
    }
  }, []);
}
