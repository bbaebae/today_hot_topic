import { useState, useEffect } from 'react';
import type { User } from '../types/user';
import { fetchUserProfile } from '../services/rewardService';

export function useProfile() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    fetchUserProfile()
      .then((data) => {
        const d = data as { user: User };
        setUser(d.user);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : '불러오기 실패');
      })
      .finally(() => setIsLoading(false));
  }, []);

  return { user, isLoading, error };
}
