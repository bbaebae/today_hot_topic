import { useState, useEffect, useCallback } from 'react';
import { IAP } from '@apps-in-toss/web-framework';
import { post } from '../services/api';

const DOPAMINE_PASS_SKU = import.meta.env.VITE_DOPAMINE_PASS_SKU ?? 'dopamine-pass';

export type IAPStatus = 'idle' | 'loading' | 'success' | 'error';

export function useIAP(onPremiumActivated?: () => void) {
  const [status, setStatus] = useState<IAPStatus>('idle');
  const [price, setPrice] = useState<string>('');
  const [isSupported, setIsSupported] = useState(false);

  // 1. 상품 목록 가져오기
  useEffect(() => {
    if (!IAP) return;

    async function load() {
      try {
        const response = await IAP!.getProductItemList();
        const products = response?.products ?? [];
        const pass = products.find((p) => p.sku === DOPAMINE_PASS_SKU);
        if (pass) {
          setPrice(pass.displayAmount);
          setIsSupported(true);
        }
      } catch {
        // 토스 앱 환경이 아님
      }
    }
    load();
  }, []);

  // 2. 인앱결제 요청하기
  const purchase = useCallback(() => {
    if (!IAP) return;
    setStatus('loading');

    const cleanup = IAP.createOneTimePurchaseOrder({
      options: {
        sku: DOPAMINE_PASS_SKU,
        // processProductGrant: 30초 내에 true를 반환해야 함
        processProductGrant: async ({ orderId }) => {
          try {
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
      onError: (error) => {
        console.error('[IAP] 결제 실패:', error);
        setStatus('error');
        cleanup();
      },
    });
  }, [onPremiumActivated]);

  // 3. 주문 복원하기: 앱 시작 시 미결 주문 처리
  useEffect(() => {
    if (!IAP) return;

    async function recoverPendingOrders() {
      try {
        const result = await IAP!.getPendingOrders();
        const orders = result?.orders ?? [];
        if (orders.length === 0) return;

        let recovered = false;
        for (const order of orders) {
          try {
            await post('/users/me/premium', {
              order_id: order.orderId,
              sku: order.sku ?? DOPAMINE_PASS_SKU,
            });
            await IAP!.completeProductGrant({ params: { orderId: order.orderId } });
            recovered = true;
          } catch {
            // 개별 주문 복원 실패는 무시
          }
        }

        if (recovered) {
          onPremiumActivated?.();
        }
      } catch {
        // 복원 실패 무시
      }
    }

    recoverPendingOrders();
  }, [onPremiumActivated]);

  return { status, price, isSupported, purchase };
}
