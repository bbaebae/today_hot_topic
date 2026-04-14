import { useState } from 'react';
import { safeHaptic } from '../utils/toss';
import type { VoteResponse } from '../types/api';
import { submitVote } from '../services/voteService';

export function useVote() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<VoteResponse | null>(null);

  const submit = async (
    pollId: string,
    option: 'A' | 'B'
  ): Promise<VoteResponse> => {
    setIsSubmitting(true);
    try {
      const res = await submitVote(pollId, option);
      setResult(res);
      safeHaptic({ type: 'softMedium' });
      return res;
    } finally {
      setIsSubmitting(false);
    }
  };

  return { submit, isSubmitting, result };
}
