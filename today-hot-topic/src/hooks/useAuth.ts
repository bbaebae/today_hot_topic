/**
 * Toss appLogin() → 서버 JWT 교환 훅.
 *
 * 흐름:
 *  1. appLogin() SDK 호출 → authorizationCode
 *  2. POST /api/v1/auth/token → 서버 JWT 수신
 *  3. Storage에 JWT 저장 → 이후 API 요청에 자동 첨부
 */
import { useState, useEffect } from 'react';
import { appLogin, Storage } from '@apps-in-toss/web-framework';

const TOKEN_KEY = 'server_jwt';
const IS_MOCK = import.meta.env.PUBLIC_USE_MOCK === 'true';

export function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(!IS_MOCK);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (IS_MOCK) return;

    Storage.getItem(TOKEN_KEY)
      .then((saved) => {
        if (saved) {
          setToken(saved);
          setIsLoading(false);
        } else {
          return login();
        }
      })
      .catch(() => login());
  }, []);

  async function login() {
    setIsLoading(true);
    setError(null);
    try {
      // Step 1: Toss SDK 로그인 → authorizationCode
      const { authorizationCode, referrer } = await appLogin();

      // Step 2: 서버에서 JWT 교환
      const resp = await fetch('/api/v1/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ authorization_code: authorizationCode, referrer }),
      });

      if (!resp.ok) throw new Error('Token exchange failed');
      const { access_token } = await resp.json();

      // Step 3: Storage 저장
      await Storage.setItem(TOKEN_KEY, access_token);
      setToken(access_token);
    } catch (e) {
      setError(e instanceof Error ? e.message : '로그인 실패');
    } finally {
      setIsLoading(false);
    }
  }

  async function logout() {
    await Storage.removeItem(TOKEN_KEY);
    setToken(null);
    await login();
  }

  return { token, isLoading, error, logout };
}
