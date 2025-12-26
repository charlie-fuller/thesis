'use client';

import { memo } from 'react';
import { useFetchData } from '@/hooks/useFetchData';
import { CardSkeleton } from './CardSkeleton';
import { ErrorWithRetry } from './ErrorWithRetry';

interface ActivityData {
  total_conversations: number;
  total_messages: number;
  documents_uploaded: number;
  images_generated: number;
  time_period: string;
}

interface ActivitySummaryCardProps {
  timePeriod?: 'week' | 'month' | 'all_time';
}

const ActivityIcon = (
  <svg
    className="w-5 h-5 icon-primary"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

function ActivitySummaryCard({
  timePeriod = 'month'
}: ActivitySummaryCardProps) {
  const { data, loading, error, refetch } = useFetchData<ActivityData>(
    `/api/personal-impact/activity-summary?time_period=${timePeriod}`,
    [timePeriod],
    { logPrefix: 'Activity Summary' }
  );

  if (loading) {
    return <CardSkeleton />;
  }

  if (error) {
    return (
      <ErrorWithRetry
        title="Activity Summary"
        subtitle="Your usage at a glance"
        message="Unable to load activity data."
        onRetry={refetch}
        icon={ActivityIcon}
      />
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
            {ActivityIcon}
            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Activity Summary</h3>
          </div>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Your usage at a glance</p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-900">
            {data.total_conversations}
          </div>
          <div className="text-xs text-blue-700">Conversations</div>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-900">
            {data.total_messages}
          </div>
          <div className="text-xs text-purple-700">Messages</div>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-900">
            {data.documents_uploaded}
          </div>
          <div className="text-xs text-green-700">Documents</div>
        </div>
        <div className="p-3 bg-orange-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-900">
            {data.images_generated}
          </div>
          <div className="text-xs text-orange-700">Images Created</div>
        </div>
      </div>
    </div>
  );
}

export default memo(ActivitySummaryCard);
