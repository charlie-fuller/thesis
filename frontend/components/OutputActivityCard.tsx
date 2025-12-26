'use client';

import { ReactElement, memo, useMemo } from 'react';
import { useFetchData } from '@/hooks/useFetchData';
import { CardSkeleton } from './CardSkeleton';
import { ErrorWithRetry } from './ErrorWithRetry';

interface OutputActivityData {
  user_id: string;
  time_period: string;
  conversations_with_output: number;
  total_conversations: number;
  output_rate: number;
  by_method: Record<string, number>;
  trend_data: Array<{
    week: string;
    total: number;
    with_output: number;
    rate: number;
  }>;
}

interface OutputActivityCardProps {
  timePeriod?: 'week' | 'month' | 'all_time';
  userId?: string;
}

const OutputIcon = (
  <svg
    className="w-5 h-5 text-primary-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    role="img"
    aria-label="Output activity icon"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

function OutputActivityCard({ timePeriod = 'month', userId }: OutputActivityCardProps) {
  // Build endpoint with optional userId
  const endpoint = useMemo(() => {
    const params = new URLSearchParams({ time_period: timePeriod });
    if (userId) {
      params.append('user_id', userId);
    }
    return `/api/kpis/output-activity?${params.toString()}`;
  }, [timePeriod, userId]);

  const { data, loading, error, refetch } = useFetchData<OutputActivityData>(
    endpoint,
    [timePeriod, userId],
    { logPrefix: 'Output Activity' }
  );

  const getStatusColor = (rate: number): string => {
    if (rate >= 50) return 'text-green-600';
    if (rate >= 25) return 'text-yellow-600';
    return 'text-orange-600';
  };

  const getStatusText = (rate: number): string => {
    if (rate >= 50) return 'Strong';
    if (rate >= 25) return 'Moderate';
    if (rate > 0) return 'Building';
    return 'No Data';
  };

  const getStatusIcon = (rate: number): ReactElement => {
    if (rate >= 50) {
      return (
        <svg
          className="w-5 h-5 text-green-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          role="img"
          aria-label="Strong output activity"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    }
    if (rate >= 25) {
      return (
        <svg
          className="w-5 h-5 text-yellow-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          role="img"
          aria-label="Moderate output activity"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      );
    }
    return (
      <svg
        className="w-5 h-5 text-orange-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        role="img"
        aria-label="Low output activity"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  };

  const formatMethodName = (method: string): string => {
    const names: Record<string, string> = {
      'copy_event': 'Copied content',
      'keyword_detected': 'Positive feedback',
      'conversation_ended': 'Completed session',
      'user_marked': 'User marked useful',
      'unknown': 'Other'
    };
    return names[method] || method.replace(/_/g, ' ');
  };

  if (loading) {
    return <CardSkeleton />;
  }

  if (error) {
    return (
      <ErrorWithRetry
        title="Output Activity"
        subtitle="Conversations producing useable materials"
        message="Unable to load output activity data."
        onRetry={refetch}
        icon={OutputIcon}
      />
    );
  }

  if (!data || data.total_conversations === 0) {
    return (
      <div className="card p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {OutputIcon}
              <h3 className="text-sm font-semibold text-primary">Output Activity</h3>
            </div>
            <p className="text-xs text-muted">Conversations producing useable materials</p>
          </div>
        </div>

        <div className="text-3xl font-bold text-primary mb-1">
          0
          <span className="text-sm font-normal text-muted ml-2">outputs</span>
        </div>

        <div className="text-sm text-secondary mb-4">
          No conversations recorded yet.
        </div>

        <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border-default)' }}>
          <p className="text-xs text-secondary">
            <strong>How it works:</strong> This metric tracks when users produce tangible outputs -
            copying generated content, confirming usefulness, or completing productive sessions.
            Higher numbers indicate the platform is delivering valuable materials.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {OutputIcon}
            <h3 className="text-sm font-semibold text-primary">Output Activity</h3>
          </div>
          <p className="text-xs text-muted">Conversations producing useable materials</p>
        </div>

        <div className="flex items-center gap-1">
          {getStatusIcon(data.output_rate)}
        </div>
      </div>

      {/* Main Metrics */}
      <div className="mb-4">
        <div className="text-3xl font-bold text-primary mb-1">
          {data.conversations_with_output}
          <span className="text-sm font-normal text-muted ml-2">
            of {data.total_conversations} conversations
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-lg font-semibold" style={{ color: 'var(--color-primary)' }}>
            {data.output_rate}%
          </div>
          <span className="text-sm text-muted">output rate</span>
        </div>
      </div>

      {/* Method Breakdown */}
      {Object.keys(data.by_method).length > 0 && (
        <div className="border-t border-default pt-4 mb-4">
          <div className="text-xs font-semibold text-muted mb-2">How outputs were detected</div>
          <div className="space-y-2">
            {Object.entries(data.by_method)
              .sort((a, b) => b[1] - a[1])
              .map(([method, count]) => {
                const percentage = data.conversations_with_output > 0
                  ? Math.min(100, Math.max(0, (count / data.conversations_with_output) * 100))
                  : 0;
                const displayWidth = percentage < 5 && percentage > 0 ? 5 : percentage;

                return (
                  <div key={method} className="flex items-center gap-2">
                    <div className="text-xs text-muted w-28 flex-shrink-0">{formatMethodName(method)}</div>
                    <div className="flex-1 rounded-full h-3 relative overflow-hidden" style={{ backgroundColor: 'var(--color-border-default)' }}>
                      <div
                        className="absolute top-0 left-0 h-full rounded-full transition-all duration-300"
                        style={{ width: `${displayWidth}%`, backgroundColor: 'var(--color-primary)' }}
                        role="progressbar"
                        aria-valuenow={percentage}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-label={`${formatMethodName(method)}: ${percentage.toFixed(1)}%`}
                      />
                    </div>
                    <div className="text-xs text-muted w-8 text-right flex-shrink-0">{count}</div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Status Indicator */}
      <div className="pt-4 border-t border-default">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted">Platform productivity</span>
          <span className={getStatusColor(data.output_rate)}>
            {getStatusText(data.output_rate)}
          </span>
        </div>

        {/* Performance Messages */}
        {data.output_rate >= 50 && (
          <div className="mt-3 p-3 rounded-lg border-l-4 border-green-500" style={{ backgroundColor: 'var(--color-bg-page)' }}>
            <p className="text-xs text-secondary">
              <strong className="text-green-500">Strong output rate!</strong> Users are consistently
              generating valuable training materials and learning content. The platform is effectively
              supporting the creation of tangible deliverables.
            </p>
          </div>
        )}
        {data.output_rate >= 25 && data.output_rate < 50 && (
          <div className="mt-3 p-3 rounded-lg border-l-4 border-yellow-500" style={{ backgroundColor: 'var(--color-bg-page)' }}>
            <p className="text-xs text-secondary">
              <strong className="text-yellow-500">Moderate output activity.</strong> Users are producing
              useable materials from their conversations. Consider reviewing conversations without detected
              outputs to identify opportunities for better prompting or system guidance.
            </p>
          </div>
        )}
        {data.output_rate > 0 && data.output_rate < 25 && (
          <div className="mt-3 p-3 rounded-lg border-l-4 border-orange-500" style={{ backgroundColor: 'var(--color-bg-page)' }}>
            <p className="text-xs text-secondary">
              <strong className="text-orange-500">Output rate is building.</strong> Many conversations
              aren&apos;t yet producing detected outputs. This could indicate users are exploring or learning,
              or that the system needs better guidance to help users generate actionable training materials.
            </p>
          </div>
        )}

        <div className="mt-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border-default)' }}>
          <p className="text-xs text-secondary">
            <strong>What this measures:</strong> Output Activity tracks conversations where users
            generated tangible materials - training content, learning approaches, or strategic documents
            they found valuable enough to copy or explicitly confirm as useful. A higher rate indicates
            the platform is effectively helping users produce deliverables.
          </p>
        </div>
      </div>
    </div>
  );
}

export default memo(OutputActivityCard);
