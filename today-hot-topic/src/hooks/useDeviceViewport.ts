import { useEffect } from 'react';
import { getPlatformOS } from '@apps-in-toss/web-framework';

export function useDeviceViewport() {
  useEffect(() => {
    const isIOS = getPlatformOS() === 'ios';

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
