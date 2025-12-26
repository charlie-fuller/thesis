'use client';

import { memo } from 'react';
import { useFetchData } from '@/hooks/useFetchData';

interface TrendDataPoint {
  week: string;
  started: number;
  completed: number;
}

interface DesignVelocityData {
  projects_started: number;
  projects_completed: number;
  completion_rate: number;
  avg_conversation_turns: number;
  projects_per_week: number;
  trend_data: TrendDataPoint[];
  time_period: string;
}

interface DesignVelocityCardProps {
  timePeriod?: 'week' | 'month' | 'all_time';
}

function DesignVelocityCard({
  timePeriod = 'month'
}: DesignVelocityCardProps) {
  const { data, loading, error, refetch } = useFetchData<DesignVelocityData>(
    `/api/personal-impact/design-velocity?time_period=${timePeriod}`,
    [timePeriod],
    { logPrefix: 'Design Velocity' }
  );

  if (loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-default p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card rounded-lg shadow-sm border border-default p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <svg
                className="w-5 h-5 icon-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Design Velocity</h3>
            </div>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Projects started and completed</p>
          </div>
        </div>

        <div className="text-sm mb-3" style={{ color: 'var(--color-text-secondary)' }}>
          Unable to load design velocity data.
        </div>
        <button
          onClick={refetch}
          className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="bg-card rounded-lg shadow-sm border border-default p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <svg
              className="w-5 h-5 icon-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Design Velocity</h3>
          </div>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Projects started and completed</p>
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {data.projects_started}
          </div>
          <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            Projects Started
          </div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {data.projects_completed}
          </div>
          <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            Completed
          </div>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-lg font-semibold text-blue-900">
            {data.completion_rate}%
          </div>
          <div className="text-xs text-blue-700">Completion Rate</div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <div className="text-lg font-semibold text-purple-900">
            {data.avg_conversation_turns}
          </div>
          <div className="text-xs text-purple-700">Avg Turns</div>
        </div>
      </div>

      {/* Trend Visualization */}
      {data.trend_data && data.trend_data.length > 0 && (
        <div className="border-t border-default pt-4">
          <div className="text-xs font-semibold text-secondary mb-2">Recent Trend</div>
          <div className="bg-gray-50 p-2 rounded-lg">
            <div className="flex items-end gap-1.5 h-20 mb-1">
              {data.trend_data.slice(-8).map((point, idx) => {
                const maxCount = Math.max(...data.trend_data.map(p => p.started));
                const height = maxCount > 0 ? Math.min(100, Math.max(0, (point.started / maxCount) * 100)) : 0;
                const displayHeight = point.started > 0 ? Math.max(height, 10) : 2;
                const completedHeight = point.started > 0 ? (point.completed / point.started) * displayHeight : 0;

                return (
                  <div key={idx} className="flex-1 flex flex-col justify-end items-center gap-0.5">
                    <div
                      className="w-full bg-blue-400 hover:bg-blue-500 rounded-t transition-all duration-200 cursor-pointer relative group"
                      style={{ height: `${displayHeight}%` }}
                      title={`Week ${point.week}: ${point.started} started, ${point.completed} completed`}
                    >
                      {point.completed > 0 && (
                        <div
                          className="w-full bg-green-500 rounded-t"
                          style={{ height: `${(completedHeight / displayHeight) * 100}%` }}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-default">
        <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          <strong>{data.projects_per_week}</strong> projects per week on average
        </div>
      </div>
    </div>
  );
}

export default memo(DesignVelocityCard);
