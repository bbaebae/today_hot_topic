import { useState } from 'react';
import { generateHapticFeedback } from '@apps-in-toss/web-framework';
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
      generateHapticFeedback({ type: 'softMedium' });
      return res;
    } finally {
      setIsSubmitting(false);
    }
  };

  return { submit, isSubmitting, result };
}
