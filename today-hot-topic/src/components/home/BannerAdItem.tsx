import { useRef, useEffect, useState } from 'react';
import { TossAds } from '@apps-in-toss/web-framework';

const BANNER_AD_GROUP_ID =
  import.meta.env.VITE_BANNER_AD_GROUP_ID ?? 'ait-ad-test-banner-id';

export function BannerAdItem() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    try {
      if (!TossAds.attachBanner.isSupported() || !containerRef.current) return;

      const attached = TossAds.attachBanner(BANNER_AD_GROUP_ID, containerRef.current, {
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
    <li style={{ listStyle: 'none' }}>
      <div ref={containerRef} style={{ width: '100%', height: '96px' }} />
    </li>
  );
}
