import styles from './TopicSkeleton.module.css';

function SkeletonBox({
  width,
  height,
  borderRadius = 4,
}: {
  width?: string;
  height: number;
  borderRadius?: number;
}) {
  return (
    <div
      className={styles.skeletonBox}
      style={{ width: width ?? '100%', height, borderRadius }}
    />
  );
}

function SkeletonItem() {
  return (
    <li className={styles.item}>
      <SkeletonBox width="28px" height={24} borderRadius={4} />
      <div className={styles.content}>
        <SkeletonBox height={18} borderRadius={4} />
        <SkeletonBox width="60%" height={14} borderRadius={4} />
      </div>
      <SkeletonBox width="64px" height={64} borderRadius={8} />
    </li>
  );
}

export function TopicSkeleton({ count = 7 }: { count?: number }) {
  return (
    <ul className={styles.list}>
      {Array.from({ length: count }, (_, i) => (
        <SkeletonItem key={i} />
      ))}
    </ul>
  );
}
