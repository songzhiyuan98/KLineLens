/**
 * Skeleton 加载占位组件
 */

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  style?: React.CSSProperties;
}

export default function Skeleton({
  width = '100%',
  height = '1rem',
  borderRadius = '4px',
  style,
}: SkeletonProps) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: '#eaeaea',
        animation: 'pulse 1.5s ease-in-out infinite',
        ...style,
      }}
    />
  );
}

export function SkeletonText({ lines = 1 }: { lines?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height="0.875rem"
          width={i === lines - 1 && lines > 1 ? '60%' : '100%'}
        />
      ))}
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div style={{
      width: '100%',
      height: '400px',
      backgroundColor: '#fff',
      borderRadius: '8px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Skeleton width="90%" height="80%" borderRadius="4px" />
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div style={{ marginBottom: '2rem' }}>
      <Skeleton width="80px" height="0.75rem" style={{ marginBottom: '1rem' }} />
      <SkeletonText lines={3} />
    </div>
  );
}

export function DetailPageSkeleton() {
  return (
    <div style={{
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '2rem 3rem',
    }}>
      {/* Header */}
      <Skeleton width="120px" height="2rem" style={{ marginBottom: '0.5rem' }} />
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <Skeleton width="150px" height="2.5rem" />
        <Skeleton width="100px" height="1.5rem" style={{ marginTop: '0.5rem' }} />
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
        <Skeleton width="60px" height="32px" borderRadius="20px" />
        <Skeleton width="60px" height="32px" borderRadius="20px" />
        <Skeleton width="60px" height="32px" borderRadius="20px" />
      </div>

      {/* Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 280px',
        gap: '4rem',
      }}>
        {/* Left */}
        <div>
          <SkeletonChart />
          <div style={{ marginTop: '2.5rem' }}>
            <Skeleton width="80px" height="0.875rem" style={{ marginBottom: '1rem' }} />
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <Skeleton width="3rem" height="0.875rem" />
                <Skeleton height="8px" style={{ flex: 1, marginTop: '0.25rem' }} borderRadius="4px" />
                <Skeleton width="2.5rem" height="0.875rem" />
              </div>
            ))}
          </div>
          <div style={{ marginTop: '2.5rem' }}>
            <Skeleton width="80px" height="0.875rem" style={{ marginBottom: '1rem' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <Skeleton height="180px" borderRadius="8px" />
              <Skeleton height="180px" borderRadius="8px" />
            </div>
          </div>
        </div>

        {/* Right */}
        <div>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  );
}
