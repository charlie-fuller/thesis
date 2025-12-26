'use client';

import { memo } from 'react';
import { useFetchData } from '@/hooks/useFetchData';
import { CardSkeleton } from './CardSkeleton';
import { ErrorWithRetry } from './ErrorWithRetry';

interface MethodologyAdoptionData {
  addie_phases_used: Record<string, number>;
  bradbury_mentions: number;
  total_conversations: number;
  conversations_with_methodology: number;
  methodology_coverage: number;
  time_period: string;
}

interface MethodologyAdoptionCardProps {
  timePeriod?: 'week' | 'month' | 'all_time';
}

const MethodologyIcon = (
  <svg
    className="w-5 h-5 icon-primary"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const addiePhaseLabels: Record<string, string> = {
  analyze: 'Analyze',
  design: 'Design',
  develop: 'Develop',
  implement: 'Implement',
  evaluate: 'Evaluate'
};

function MethodologyAdoptionCard({
  timePeriod = 'month'
}: MethodologyAdoptionCardProps) {
  const { data, loading, error, refetch } = useFetchData<MethodologyAdoptionData>(
    `/api/personal-impact/methodology-adoption?time_period=${timePeriod}`,
    [timePeriod],
    { logPrefix: 'Methodology Adoption' }
  );

  if (loading) {
    return <CardSkeleton />;
  }

  if (error) {
    return (
      <ErrorWithRetry
        title="Methodology Adoption"
        subtitle="ADDIE & Bradbury Method usage"
        message="Unable to load methodology data."
        onRetry={refetch}
        icon={MethodologyIcon}
      />
    );
  }

  if (!data) {
    return null;
  }

  const addiePhases = Object.entries(data.addie_phases_used);
  const totalAddieUsage = addiePhases.reduce((sum, [, count]) => sum + count, 0);

  return (
    <div className="bg-card rounded-lg shadow-sm border border-default p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {MethodologyIcon}
            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Methodology Adoption</h3>
          </div>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>ADDIE & Bradbury Method usage</p>
        </div>
      </div>

      {/* Coverage Metric */}
      <div className="mb-4">
        <div className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
          {data.methodology_coverage}%
        </div>
        <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          Conversations using L&D methodology
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(data.methodology_coverage, 100)}%` }}
          />
        </div>
      </div>

      {/* ADDIE Phases */}
      <div className="mb-4">
        <div className="text-xs font-semibold text-secondary mb-2">ADDIE Phases Used</div>
        {addiePhases.length > 0 ? (
          <div className="space-y-2">
            {addiePhases.map(([phase, count]) => {
              const percentage = totalAddieUsage > 0 ? (count / totalAddieUsage) * 100 : 0;
              return (
                <div key={phase} className="flex items-center gap-2">
                  <div className="w-20 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                    {addiePhaseLabels[phase] || phase}
                  </div>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                      title={`${count} mentions`}
                    />
                  </div>
                  <div className="w-8 text-xs text-right" style={{ color: 'var(--color-text-secondary)' }}>
                    {count}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-xs text-gray-500 italic p-3 bg-gray-50 rounded">
            No ADDIE phases detected yet. Try discussing instructional design concepts!
          </div>
        )}
      </div>

      {/* Bradbury Method */}
      <div className="border-t border-default pt-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-secondary mb-1">Bradbury Method</div>
            <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              Behavior change principles
            </div>
          </div>
          <div className="text-2xl font-bold text-purple-600">
            {data.bradbury_mentions}
          </div>
        </div>

        {data.bradbury_mentions > 0 && (
          <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <p className="text-xs text-purple-900">
              Great work applying behavior change principles! The Bradbury Method focuses on creating lasting impact.
            </p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-default">
        <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          {data.conversations_with_methodology} of {data.total_conversations} conversations used L&D methodologies
        </div>
      </div>
    </div>
  );
}

export default memo(MethodologyAdoptionCard);
