'use client';

import { memo } from 'react';
import { useFetchData } from '@/hooks/useFetchData';
import { CardSkeleton } from './CardSkeleton';
import { ErrorWithRetry } from './ErrorWithRetry';

interface DimensionData {
  label: string;
  description: string;
  score: number;
  conversations_count: number;
}

interface SystemsThinkingData {
  overall_score: number;
  dimensions: Record<string, DimensionData>;
  total_conversations: number;
  conversations_with_design_thinking: number;
  time_period: string;
}

interface SystemsThinkingCardProps {
  timePeriod?: 'week' | 'month' | 'all_time';
}

const ThinkingIcon = (
  <svg
    className="w-5 h-5 icon-primary"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

// Color coding for dimension scores
function getScoreColor(score: number): string {
  if (score >= 60) return 'text-green-600';
  if (score >= 30) return 'text-yellow-600';
  return 'text-gray-400';
}

function getBarColor(score: number): string {
  if (score >= 60) return 'bg-green-500';
  if (score >= 30) return 'bg-yellow-500';
  return 'bg-gray-300';
}

function SystemsThinkingCard({
  timePeriod = 'month'
}: SystemsThinkingCardProps) {
  const { data, loading, error, refetch } = useFetchData<SystemsThinkingData>(
    `/api/personal-impact/systems-thinking-score?time_period=${timePeriod}`,
    [timePeriod],
    { logPrefix: 'Systems Thinking Score' }
  );

  if (loading) {
    return <CardSkeleton rows={3} />;
  }

  if (error) {
    return (
      <ErrorWithRetry
        title="Learning Systems Thinking"
        subtitle="Quality of design considerations"
        message="Unable to load systems thinking data."
        onRetry={refetch}
        icon={ThinkingIcon}
      />
    );
  }

  if (!data) {
    return null;
  }

  // Order dimensions for display
  const dimensionOrder = [
    'learner_focus',
    'outcome_orientation',
    'transfer_application',
    'engagement_design',
    'retention_reinforcement',
    'feedback_assessment'
  ];

  return (
    <div className="bg-card rounded-lg shadow-sm border border-default p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {ThinkingIcon}
            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              Learning Systems Thinking
            </h3>
          </div>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            Quality of design considerations
          </p>
        </div>
      </div>

      {/* Overall Score */}
      <div className="mb-6">
        <div className="flex items-baseline gap-2">
          <span className={`text-4xl font-bold ${getScoreColor(data.overall_score)}`}>
            {data.overall_score}%
          </span>
          <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            overall
          </span>
        </div>
        <div className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          {data.conversations_with_design_thinking} of {data.total_conversations} conversations show design thinking
        </div>
      </div>

      {/* Dimension Breakdown */}
      <div className="space-y-3">
        {dimensionOrder.map((dimKey) => {
          const dim = data.dimensions[dimKey];
          if (!dim) return null;

          return (
            <div key={dimKey}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium" style={{ color: 'var(--color-text-primary)' }}>
                  {dim.label}
                </span>
                <span className={`text-xs font-semibold ${getScoreColor(dim.score)}`}>
                  {dim.score}%
                </span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${getBarColor(dim.score)}`}
                  style={{ width: `${Math.max(dim.score, 2)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer explanation */}
      <div className="mt-4 pt-4 border-t border-default">
        <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          Measures how often your conversations address key instructional design considerations
        </p>
      </div>
    </div>
  );
}

export default memo(SystemsThinkingCard);
