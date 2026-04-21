import type { VoteResponse } from '../types/api';
import { USE_MOCK, delay, post } from './api';

export async function submitVote(
  pollId: string,
  selectedOption: 'A' | 'B'
): Promise<VoteResponse> {
  if (USE_MOCK) {
    await delay(500);

    // Mock: 옵션 A 선택 시 A 카운트 증가
    return {
      pollId,
      selectedOption,
      optionACount: selectedOption === 'A' ? 8235 : 8234,
      optionBCount: selectedOption === 'B' ? 1877 : 1876,
    };
  }

  return post<VoteResponse, { selected_option: string }>(
    `/polls/${pollId}/vote`,
    { selected_option: selectedOption }
  );
}
