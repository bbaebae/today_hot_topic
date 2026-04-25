// v2: RichBody inline image rendering
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTopicDetail } from '../hooks/useTopicDetail';
import { useVote } from '../hooks/useVote';
import { NavBar } from '../components/layout/NavBar';
import { SummaryCard } from '../components/detail/SummaryCard';
import { PollSection } from '../components/detail/PollSection';
import styles from './DetailPage.module.css';

const IMG_MARKER_RE = /(\[IMG:[^\]]+\])/;

function hasInlineImages(body: string) {
  return body?.includes('[IMG:');
}

function RichBody({ body }: { body: string }) {
  const segments = body.split(IMG_MARKER_RE);
  return (
    <div className={styles.richBody}>
      {segments.map((seg, i) => {
        const trimmed = seg.trim();
        // [IMG:url] 마커 판별: trim 후 startsWith/endsWith로 체크 (정규식 newline 이슈 방지)
        if (trimmed.startsWith('[IMG:') && trimmed.endsWith(']')) {
          const src = trimmed.slice(5, -1).trim();
          if (src) {
            return (
              <img
                key={i}
                src={src}
                alt=""
                className={styles.inlineImage}
                referrerPolicy="no-referrer"
              />
            );
          }
        }
        if (!trimmed) return null;
        return (
          <p key={i} className={styles.bodyText}>
            {trimmed}
          </p>
        );
      })}
    </div>
  );
}

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

  const hasComments = (topic?.topComments?.length ?? 0) > 0;

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

            {/* AI 3줄 요약 */}
            <SummaryCard
              summaries={topic.summary}
              sourceUrl={topic.sourceUrl}
              createdAt={topic.createdAt}
            />

            {/* 본문 (인라인 이미지 포함) */}
            {topic.body && hasInlineImages(topic.body) ? (
              <RichBody body={topic.body} />
            ) : (
              <>
                {/* 레거시: 이미지 상단 고정 (인라인 마커 없는 구 데이터) */}
                {(topic.imageUrls?.length > 0 || topic.imageUrl) && (
                  <div className={styles.imageList}>
                    {(topic.imageUrls?.length > 0 ? topic.imageUrls : [topic.imageUrl]).filter(Boolean).map((url, i) => (
                      <img
                        key={i}
                        src={url!}
                        alt={`${topic.title} 이미지 ${i + 1}`}
                        className={styles.image}
                        referrerPolicy="no-referrer"
                        onError={(e) => { e.currentTarget.style.display = 'none'; }}
                      />
                    ))}
                  </div>
                )}
                {topic.body && (
                  <div className={styles.bodySection}>
                    <p className={styles.bodyText}>{topic.body}</p>
                  </div>
                )}
              </>
            )}

            {/* 베스트댓글 — story(커뮤니티) 카테고리만 표시 */}
            {hasComments && topic.category === 'story' && (
              <>
                <div className={styles.commentSectionHeader}>베스트 댓글</div>
                <div className={styles.commentList}>
                  {topic.topComments!.map((comment, i) => (
                    <div key={i} className={styles.commentItem}>
                      <span className={`${styles.commentRank} ${i < 3 ? styles.top : ''}`}>
                        {i + 1}
                      </span>
                      <p className={styles.commentText}>{comment}</p>
                    </div>
                  ))}
                </div>
              </>
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
