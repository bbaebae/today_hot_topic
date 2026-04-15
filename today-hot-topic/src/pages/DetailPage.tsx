import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTopicDetail } from '../hooks/useTopicDetail';
import { useVote } from '../hooks/useVote';
import { useReward } from '../hooks/useReward';
import { NavBar } from '../components/layout/NavBar';
import { SummaryCard } from '../components/detail/SummaryCard';
import { PollSection } from '../components/detail/PollSection';
import { RewardModal } from '../components/detail/RewardModal';
import { AdConfirmModal } from '../components/detail/AdConfirmModal';
import styles from './DetailPage.module.css';

function DetailSkeleton() {
  return (
    <div className={styles.skeleton}>
      {[120, 80, '100%', 200, 140].map((w, i) => (
        <div
          key={i}
          className={styles.skeletonBox}
          style={{
            width: typeof w === 'number' ? `${w}px` : w,
            height: i === 3 ? 160 : 20,
            borderRadius: i === 3 ? 16 : 4,
          }}
        />
      ))}
    </div>
  );
}

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { topic, isLoading, error, hasVoted, votedOption, markVoted } =
    useTopicDetail(id ?? '');
  const { submit, isSubmitting } = useVote();
  const { isModalOpen, amount, balance, isDailyLimitReached, claim, closeModal } =
    useReward();
  const [adConfirmOpen, setAdConfirmOpen] = useState(false);
  const [pendingPollId, setPendingPollId] = useState<string | null>(null);

  const handleVote = async (option: 'A' | 'B') => {
    if (!topic) return;
    markVoted(option);
    const result = await submit(topic.poll.id, option);
    if (result.rewardEligible && !isDailyLimitReached) {
      setPendingPollId(topic.poll.id);
      setAdConfirmOpen(true);
    }
  };

  const handleAdConfirm = async () => {
    setAdConfirmOpen(false);
    if (pendingPollId) {
      await claim('ad', pendingPollId);
      setPendingPollId(null);
    }
  };

  const handleAdCancel = () => {
    setAdConfirmOpen(false);
    setPendingPollId(null);
  };

  if (error) {
    return (
      <div className={styles.page}>
        <NavBar showBack onBack={() => navigate(-1)} />
        <div className={styles.errorState}>
          <p>불러오기 실패 😢</p>
          <button onClick={() => navigate(-1)}>돌아가기</button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <NavBar
        showBack
        showShare
        onBack={() => navigate(-1)}
      />

      <div className={styles.scrollArea}>
        {isLoading || !topic ? (
          <DetailSkeleton />
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
          >
            {/* 헤더 영역 */}
            <div className={styles.topicHeader}>
              <h2 className={styles.title}>{topic.title}</h2>
            </div>

            {/* 썸네일 */}
            {topic.imageUrl && (
              <div className={styles.imageWrap}>
                <img src={topic.imageUrl} alt={topic.title} className={styles.image} />
              </div>
            )}

            {/* AI 3줄 요약 */}
            <SummaryCard
              summaries={topic.summary}
              sourceUrl={topic.sourceUrl}
              createdAt={topic.createdAt}
            />

            {/* 투표 섹션 */}
            <PollSection
              poll={topic.poll}
              hasVoted={hasVoted}
              votedOption={votedOption}
              onVote={handleVote}
              isSubmitting={isSubmitting}
            />

            {/* 일일 한도 메시지 */}
            {isDailyLimitReached && (
              <div className={styles.limitBanner}>
                🎯 오늘의 포인트는 다 받았어요 (하루 3회 한도)
              </div>
            )}

            <div className={styles.bottomSpacer} />
          </motion.div>
        )}
      </div>

      {/* 광고 확인 팝업 */}
      <AdConfirmModal
        isOpen={adConfirmOpen}
        onConfirm={handleAdConfirm}
        onCancel={handleAdCancel}
      />

      {/* 보상 모달 */}
      <RewardModal
        isOpen={isModalOpen}
        onClose={closeModal}
        amount={amount}
        balance={balance}
      />
    </div>
  );
}
