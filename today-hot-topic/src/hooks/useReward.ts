import { useState } from 'react';
import { safeHaptic } from '../utils/toss';
import type { RewardType } from '../types/user';
import { claimReward } from '../services/rewardService';

export function useReward() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [amount, setAmount] = useState(10);
  const [balance, setBalance] = useState(1230);
  const [isDailyLimitReached, setIsDailyLimitReached] = useState(false);

  const claim = async (rewardType: RewardType, referenceId: string) => {
    try {
      const res = await claimReward(rewardType, referenceId);
      setAmount(res.amount);
      setBalance(res.currentBalance);
      setIsModalOpen(true);
      safeHaptic({ type: 'success' });
    } catch (e) {
      const err = e as { status?: number };
      if (err.status === 429) {
        setIsDailyLimitReached(true);
      }
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  return {
    isModalOpen,
    amount,
    balance,
    isDailyLimitReached,
    claim,
    closeModal,
  };
}
