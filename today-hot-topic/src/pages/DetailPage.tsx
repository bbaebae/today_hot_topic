import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { loadFullScreenAd, showFullScreenAd } from '@apps-in-toss/web-framework';
import { useTopicDetail } from '../hooks/useTopicDetail';
import { useVote } from '../hooks/useVote';
import { useReward } from '../hooks/useReward';
import { NavBar } from '../components/layout/NavBar';
import { safeOpenUrl } from '../utils/toss';
import { SummaryCard } from '../components/detail/SummaryCard';
import { PollSection } from '../components/detail/PollSection';
import { RewardModal } from '../components/detail/RewardModal';
import { AdConfirmModal } from '../components/detail/AdConfirmModal';
import styles from './DetailPage.module.css';

const AD_GROUP_ID = import.meta.env.VITE_AD_GROUP_ID ?? 'ait-ad-test-rewarded-id';

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
  const isAdLoaded = useRef(false);

  // 광고 미리 로드
  useEffect(() => {
    try {
      if (!loadFullScreenAd.isSupported()) return;
      const unregister = loadFullScreenAd({
        options: { adGroupId: AD_GROUP_ID },
        onEvent: (event) => {
          if (event.type === 'loaded') isAdLoaded.current = true;
        },
        onError: () => { isAdLoaded.current = false; },
      });
      return () => unregister();
    } catch {
      // not in Toss app environment
    }
  }, []);

  const handleVote = async (option: 'A' | 'B') => {
    if (!topic) return;
    markVoted(option);
    const result = await submit(topic.poll.id, option);
    if (result.rewardEligible && !isDailyLimitReached) {
      setPendingPollId(topic.poll.id);
      setAdConfirmOpen(true);
    }
  };

  const handleAdConfirm = (pollId: string) => {
    setAdConfirmOpen(false);
    try {
      if (!showFullScreenAd.isSupported() || !isAdLoaded.current) return;
    } catch {
      return;
    }

    showFullScreenAd({
      options: { adGroupId: AD_GROUP_ID },
      onEvent: (event) => {
        if (event.type === 'userEarnedReward') {
          claim('ad', pollId);
        }
        if (event.type === 'dismissed') {
          isAdLoaded.current = false;
          // 다음 광고 미리 로드
          loadFullScreenAd({
            options: { adGroupId: AD_GROUP_ID },
            onEvent: (e) => { if (e.type === 'loaded') isAdLoaded.current = true; },
            onError: () => {},
          });
        }
      },
      onError: () => {},
    });
    setPendingPollId(null);
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

            {/* 이미지 목록 */}
            {(topic.imageUrls?.length > 0 || topic.imageUrl) && (
              <div className={styles.imageList}>
                {(topic.imageUrls?.length > 0 ? topic.imageUrls : [topic.imageUrl]).filter(Boolean).map((url, i) => (
                  <img
                    key={i}
                    src={url!}
                    alt={`${topic.title} 이미지 ${i + 1}`}
                    className={styles.image}
                    referrerPolicy="no-referrer"
                  />
                ))}
              </div>
            )}

            {/* AI 3줄 요약 */}
            <SummaryCard
              summaries={topic.summary}
              sourceUrl={topic.sourceUrl}
              createdAt={topic.createdAt}
            />

            {/* 본문 */}
            {topic.body && (
              <div className={styles.bodySection}>
                <p className={styles.bodyText}>{topic.body}</p>
              </div>
            )}

            <div className={styles.bottomSpacer} />
          </motion.div>
        )}
      </div>

      {/* 하단 고정 투표 섹션 */}
      {topic && (
        <div className={styles.stickyPoll}>
          {isDailyLimitReached && (
            <div className={styles.limitBanner}>
              🎯 오늘의 포인트는 다 받았어요 (하루 3회 한도)
            </div>
          )}
          <PollSection
            poll={topic.poll}
            hasVoted={hasVoted}
            votedOption={votedOption}
            onVote={handleVote}
            isSubmitting={isSubmitting}
          />
        </div>
      )}

      {/* 광고 확인 팝업 */}
      <AdConfirmModal
        isOpen={adConfirmOpen}
        onConfirm={() => pendingPollId && handleAdConfirm(pendingPollId)}
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
