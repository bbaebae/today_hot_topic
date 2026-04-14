/**
 * @apps-in-toss/web-framework의 네이티브 브리지 함수들은
 * Toss 앱 환경 밖(일반 브라우저)에서 호출 시 throw합니다.
 * 이 유틸리티는 각 함수를 안전하게 감싸서 브라우저에서도 무해하게 동작하도록 합니다.
 */
import { generateHapticFeedback, Storage } from '@apps-in-toss/web-framework';

type HapticType = Parameters<typeof generateHapticFeedback>[0];

export function safeHaptic(options: HapticType): void {
  try {
    // generateHapticFeedback은 Promise를 반환하며 브라우저 환경에서 async로 reject합니다.
    // 동기 catch 외에 Promise rejection도 반드시 삼켜야 합니다.
    const result = generateHapticFeedback(options) as unknown;
    if (result instanceof Promise) {
      result.catch(() => {});
    }
  } catch {
    // Toss 앱 환경 밖에서는 무시
  }
}

export const safeStorage = {
  getItem: async (key: string): Promise<string | null> => {
    try {
      return await Storage.getItem(key);
    } catch {
      return localStorage.getItem(key);
    }
  },
  setItem: async (key: string, value: string): Promise<void> => {
    try {
      await Storage.setItem(key, value);
    } catch {
      localStorage.setItem(key, value);
    }
  },
  removeItem: async (key: string): Promise<void> => {
    try {
      await Storage.removeItem(key);
    } catch {
      localStorage.removeItem(key);
    }
  },
};
