'use client';

import { memo, useMemo } from 'react';
import { useFetchData } from '@/hooks/useFetchData';
import { CardSkeleton } from './CardSkeleton';
import { ErrorWithRetry } from './ErrorWithRetry';

interface TrendDataPoint {
  week: string;
  count: number;
}

interface IdeationVelocityData {
  user_id: string;
  time_period: string;
  drafts_initiated: number;
  avg_per_week: number;
  trend_data: TrendDataPoint[];
}

interface IdeationVelocityCardProps {
  timePeriod?: 'week' | 'month' | 'all_time';
  userId?: string;  // Optional: for admins to view specific user's data
}

const LightningIcon = (
  <svg
    className="w-5 h-5 text-primary-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    role="img"
    aria-label="Ideation velocity icon"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

function IdeationVelocityCard({
  timePeriod = 'month',
  userId
}: IdeationVelocityCardProps) {
  // Build endpoint with optional userId
  const endpoint = useMemo(() => {
    const params = new URLSearchParams({ time_period: timePeriod });
    if (userId) {
      params.append('user_id', userId);
    }
    return `/api/kpis/ideation-velocity?${params.toString()}`;
  }, [timePeriod, userId]);

  const { data, loading, error, refetch } = useFetchData<IdeationVelocityData>(
    endpoint,
    [timePeriod, userId],
    { logPrefix: 'Ideation Velocity' }
  );

  const getStatusColor = (avgPerWeek: number): string => {
    if (avgPerWeek >= 3) return 'text-green-600';
    if (avgPerWeek >= 2) return 'text-yellow-600';
    return 'text-orange-600';
  };

  const getStatusText = (avgPerWeek: number): string => {
    if (avgPerWeek >= 3) return 'Excellent';
    if (avgPerWeek >= 2) return 'Good';
    return 'Needs Improvement';
  };

  const getStatusIcon = (avgPerWeek: number) => {
    if (avgPerWeek >= 3) {
      return (
        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" role="img" aria-label="Success indicator">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    }
    if (avgPerWeek >= 2) {
      return (
        <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" role="img" aria-label="Warning indicator">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" role="img" aria-label="Needs attention indicator">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  };

  const getDateFromWeek = (weekStr: string) => {
    const [year, week] = weekStr.split('-W');
    if (!year || !week) return weekStr;
    const date = new Date(parseInt(year), 0, 1 + (parseInt(week) - 1) * 7);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (loading) {
    return <CardSkeleton />;
  }

  if (error) {
    return (
      <ErrorWithRetry
        title="Ideation Velocity"
        subtitle="Strategic drafts initiated per week"
        message="Unable to load ideation velocity data. This might be because no conversations have been created yet."
        onRetry={refetch}
        icon={LightningIcon}
      />
    );
  }

  if (!data) {
    return null;
  }

  // Show helpful message if no drafts have been initiated yet
  if (data.drafts_initiated === 0) {
    return (
      <div className="card p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {LightningIcon}
              <h3 className="text-sm font-semibold text-primary">Ideation Velocity</h3>
            </div>
            <p className="text-xs text-muted">Strategic drafts initiated per week</p>
          </div>
        </div>

        <div className="text-3xl font-bold text-primary mb-1">
          0.0
          <span className="text-sm font-normal text-muted ml-2">drafts/week</span>
        </div>

        <div className="text-sm text-secondary mb-4">
          No strategic drafts initiated yet in {data.time_period === 'all_time' ? 'all time' : `the past ${data.time_period}`}.
        </div>

        <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border-default)' }}>
          <p className="text-xs text-secondary">
            <strong>Getting Started:</strong> Start conversations with strategic keywords like &quot;draft&quot;, &quot;plan&quot;, &quot;strategy&quot;, &quot;framework&quot;, or &quot;report&quot; to track your ideation velocity.
          </p>
        </div>

        <div className="mt-4 pt-4 border-t border-default">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted">Goal: ≥ 2 drafts/week</span>
            <span className="text-orange-600">Not yet tracking</span>
          </div>
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
            {LightningIcon}
            <h3 className="text-sm font-semibold text-primary">Ideation Velocity</h3>
          </div>
          <p className="text-xs text-muted">Strategic drafts initiated per week</p>
        </div>

        <div className="flex items-center gap-1">
          {getStatusIcon(data.avg_per_week)}
        </div>
      </div>

      {/* Main Metric */}
      <div className="mb-4">
        <div className="text-3xl font-bold text-primary mb-1">
          {data.avg_per_week.toFixed(1)}
          <span className="text-sm font-normal text-muted ml-2">drafts/week</span>
        </div>
        <div className="text-sm text-muted">
          {data.drafts_initiated} total drafts in {data.time_period === 'all_time' ? 'all time' : `past ${data.time_period}`}
        </div>
      </div>

      {/* Trend Visualization */}
      {data.trend_data && data.trend_data.length > 0 && (
        <div className="border-t border-default pt-4">
          <div className="text-xs font-semibold text-muted mb-2">Recent Trend (Last 8 Weeks)</div>
          <div className="p-2 rounded-lg" style={{ backgroundColor: 'var(--color-bg-page)' }}>
            {/* Count labels */}
            <div className="flex gap-1.5 mb-1">
              {data.trend_data.slice(-8).map((point, idx) => (
                <div key={idx} className="flex-1 text-center">
                  <div className="text-[10px] font-semibold text-primary h-3">
                    {point.count > 0 ? point.count : ''}
                  </div>
                </div>
              ))}
            </div>
            {/* Bars */}
            <div className="flex items-end gap-1.5 h-20 mb-1" role="img" aria-label="Trend chart showing drafts over time">
              {data.trend_data.slice(-8).map((point, idx) => {
                const maxCount = Math.max(...data.trend_data.map(p => p.count));
                const height = maxCount > 0 ? Math.min(100, Math.max(0, (point.count / maxCount) * 100)) : 0;
                const displayHeight = point.count > 0 ? Math.max(height, 10) : 2;
                const dateLabel = getDateFromWeek(point.week);

                return (
                  <div
                    key={idx}
                    className="flex-1 rounded-t transition-all duration-200 cursor-pointer relative group"
                    style={{ height: `${displayHeight}%`, backgroundColor: 'var(--color-primary)' }}
                    title={`${dateLabel}: ${point.count} drafts`}
                    role="presentation"
                  >
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10" style={{ backgroundColor: 'var(--color-bg-card)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border-default)' }}>
                      {dateLabel}: {point.count} {point.count === 1 ? 'draft' : 'drafts'}
                    </div>
                  </div>
                );
              })}
            </div>
            {/* Date Labels */}
            <div className="flex gap-1.5">
              {data.trend_data.slice(-8).map((point, idx) => (
                <div key={idx} className="flex-1 text-center">
                  <div className="text-[10px] text-muted truncate" title={point.week}>
                    {getDateFromWeek(point.week)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Goal Indicator */}
      <div className="mt-4 pt-4 border-t border-default">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted">Goal: ≥ 2 drafts/week</span>
          <span className={getStatusColor(data.avg_per_week)}>
            {getStatusText(data.avg_per_week)}
          </span>
        </div>
        {/* Performance Messages in Boxes */}
        {data.avg_per_week >= 3 && (
          <div className="mt-3 p-3 rounded-lg border-l-4 border-green-500" style={{ backgroundColor: 'var(--color-bg-page)' }}>
            <p className="text-xs text-secondary">
              <strong className="text-green-500">Excellent velocity!</strong> Consistently using AI as a force multiplier for strategic work.
              This level of engagement demonstrates effective integration of AI-assisted ideation into regular workflows.
            </p>
          </div>
        )}
        {data.avg_per_week >= 2 && data.avg_per_week < 3 && (
          <div className="mt-3 p-3 rounded-lg border-l-4 border-yellow-500" style={{ backgroundColor: 'var(--color-bg-page)' }}>
            <p className="text-xs text-secondary">
              <strong className="text-yellow-500">Good pace!</strong> Meeting the goal for regular AI-assisted ideation.
              Continue this pattern to maintain consistent strategic output and knowledge application.
            </p>
          </div>
        )}
        {data.avg_per_week < 2 && (
          <div className="mt-3 p-3 rounded-lg border-l-4 border-orange-500" style={{ backgroundColor: 'var(--color-bg-page)' }}>
            <p className="text-xs text-secondary">
              <strong className="text-orange-500">Below target.</strong> Increasing conversation frequency will improve ideation velocity.
              Consider dedicating time for AI-assisted strategic planning and drafting sessions.
            </p>
          </div>
        )}

        <div className="mt-3 p-3 rounded-lg" style={{ backgroundColor: 'var(--color-bg-page)', border: '1px solid var(--color-border-default)' }}>
          <p className="text-xs text-secondary">
            <strong>What this measures:</strong> This metric tracks how often users initiate strategic work using the AI assistant,
            indicating force multiplier effect and knowledge application. Higher velocity shows active engagement in high-value work.
            Goal: ≥ 2 drafts per week demonstrates consistent AI-assisted ideation patterns aligned with the Bradbury Impact Loop methodology.
          </p>
        </div>
      </div>
    </div>
  );
}

export default memo(IdeationVelocityCard);
