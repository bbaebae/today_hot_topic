import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTopicDetail } from '../hooks/useTopicDetail';
import { useVote } from '../hooks/useVote';
import { NavBar } from '../components/layout/NavBar';
import { SummaryCard } from '../components/detail/SummaryCard';
import { PollSection } from '../components/detail/PollSection';
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

  const handleVote = async (option: 'A' | 'B') => {
    if (!topic) return;
    markVoted(option);
    await submit(topic.poll.id, option);
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
          <PollSection
            poll={topic.poll}
            hasVoted={hasVoted}
            votedOption={votedOption}
            onVote={handleVote}
            isSubmitting={isSubmitting}
          />
        </div>
      )}
    </div>
  );
}
