import { Storage } from '@apps-in-toss/web-framework';

const USE_MOCK = import.meta.env.PUBLIC_USE_MOCK === 'true';
const BASE_URL = '/api/v1';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  if (USE_MOCK) return {};
  const token = await Storage.getItem('server_jwt').catch(() => null);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function get<T>(path: string): Promise<T> {
  const authHeaders = await getAuthHeaders();
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw Object.assign(new Error(error.message ?? res.statusText), {
      status: res.status,
      body: error,
    });
  }

  return res.json();
}

export async function post<TResponse, TBody = unknown>(
  path: string,
  body: TBody,
): Promise<TResponse> {
  const authHeaders = await getAuthHeaders();
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw Object.assign(new Error(error.message ?? res.statusText), {
      status: res.status,
      body: error,
    });
  }

  return res.json();
}

export { USE_MOCK, delay };
