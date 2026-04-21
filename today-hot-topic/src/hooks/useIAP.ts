import { useState, useEffect, useCallback } from 'react';
import { IAP } from '@apps-in-toss/web-framework';
import { post } from '../services/api';

const DOPAMINE_PASS_SKU = import.meta.env.VITE_DOPAMINE_PASS_SKU ?? 'dopamine-pass';

export type IAPStatus = 'idle' | 'loading' | 'success' | 'error';

export function useIAP(onPremiumActivated?: () => void) {
  const [status, setStatus] = useState<IAPStatus>('idle');
  const [price, setPrice] = useState<string>('');
  const [isSupported, setIsSupported] = useState(false);

  // 상품 정보 로드 및 지원 여부 확인
  useEffect(() => {
    async function load() {
      try {
        if (!IAP) return;
        setIsSupported(true);
        const res = await IAP.getProductItemList();
        const pass = res?.products.find((p) => p.sku === DOPAMINE_PASS_SKU);
        if (pass) setPrice(pass.displayAmount);
      } catch {
        // 토스 앱 환경이 아님
      }
    }
    load();
  }, []);

  const purchase = useCallback(() => {
    if (!IAP) return;
    setStatus('loading');

    const cleanup = IAP.createOneTimePurchaseOrder({
      options: {
        sku: DOPAMINE_PASS_SKU,
        processProductGrant: async ({ orderId }) => {
          try {
            // 백엔드에 프리미엄 활성화 요청
            await post('/users/me/premium', {
              order_id: orderId,
              sku: DOPAMINE_PASS_SKU,
            });
            return true;
          } catch {
            return false;
          }
        },
      },
      onEvent: (event) => {
        if (event.type === 'success') {
          setStatus('success');
          onPremiumActivated?.();
          cleanup();
        }
      },
      onError: () => {
        setStatus('error');
        cleanup();
      },
    });
  }, [onPremiumActivated]);

  // 앱 재시작 시 미처리 주문 복구
  useEffect(() => {
    async function recoverPendingOrders() {
      try {
        if (!IAP) return;
        const pending = await IAP.getPendingOrders();
        if (!pending?.orders.length) return;

        for (const order of pending.orders) {
          try {
            await post('/users/me/premium', {
              order_id: order.orderId,
              sku: order.sku ?? DOPAMINE_PASS_SKU,
            });
            await IAP.completeProductGrant({ params: { orderId: order.orderId } });
          } catch {
            // 개별 복구 실패는 무시
          }
        }
      } catch {
        // 복구 실패 무시
      }
    }
    recoverPendingOrders();
  }, []);

  return { status, price, isSupported, purchase };
}
