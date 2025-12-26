'use client';

interface CardSkeletonProps {
  /** Number of skeleton rows to display (default: 2) */
  rows?: number;
  /** Whether to show a header row (default: true) */
  showHeader?: boolean;
  /** Custom class name for the card container */
  className?: string;
}

/**
 * Reusable loading skeleton for dashboard cards.
 * Eliminates duplicate loading state UI across card components.
 */
export function CardSkeleton({
  rows = 2,
  showHeader = true,
  className = ''
}: CardSkeletonProps) {
  return (
    <div className={`bg-card rounded-lg shadow-sm border border-default p-6 ${className}`}>
      <div className="animate-pulse">
        {showHeader && (
          <div
            className="h-4 rounded w-1/3 mb-4"
            style={{ backgroundColor: 'var(--color-border-default)' }}
          />
        )}
        {Array.from({ length: rows }).map((_, idx) => (
          <div
            key={idx}
            className={`h-8 rounded ${idx === 0 ? 'w-1/2' : 'w-2/3'} ${idx < rows - 1 ? 'mb-3' : ''}`}
            style={{ backgroundColor: 'var(--color-border-default)' }}
          />
        ))}
      </div>
    </div>
  );
}

export default CardSkeleton;
