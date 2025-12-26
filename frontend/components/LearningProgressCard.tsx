'use client';

import { memo } from 'react';
import { useFetchData } from '@/hooks/useFetchData';
import { CardSkeleton } from './CardSkeleton';
import { ErrorWithRetry } from './ErrorWithRetry';

interface GrowthTrendPoint {
  week: string;
  skills_practiced: number;
  total_mentions: number;
}

interface LearningProgressData {
  topics_explored: string[];
  skills_practiced: Record<string, number>;
  total_conversations: number;
  unique_skills: number;
  growth_trend: GrowthTrendPoint[];
  time_period: string;
}

interface LearningProgressCardProps {
  timePeriod?: 'week' | 'month' | 'all_time';
}

const TrendIcon = (
  <svg
    className="w-5 h-5 icon-primary"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

function LearningProgressCard({
  timePeriod = 'month'
}: LearningProgressCardProps) {
  const { data, loading, error, refetch } = useFetchData<LearningProgressData>(
    `/api/personal-impact/learning-progress?time_period=${timePeriod}`,
    [timePeriod],
    { logPrefix: 'Learning Progress' }
  );

  const skillLabels: Record<string, string> = {
    assessment_design: 'Assessment Design',
    objective_writing: 'Objective Writing',
    instructional_strategy: 'Instructional Strategy',
    content_design: 'Content Design',
    facilitation: 'Facilitation'
  };

  if (loading) {
    return <CardSkeleton />;
  }

  if (error) {
    return (
      <ErrorWithRetry
        title="Learning Progress"
        subtitle="Skills and growth tracking"
        message="Unable to load learning progress data."
        onRetry={refetch}
        icon={TrendIcon}
      />
    );
  }

  if (!data) {
    return null;
  }

  const skillsArray = Object.entries(data.skills_practiced).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-card rounded-lg shadow-sm border border-default p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {TrendIcon}
            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Learning Progress</h3>
          </div>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Skills and growth tracking</p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-indigo-50 rounded-lg">
          <div className="text-2xl font-bold text-indigo-900">
            {data.unique_skills}
          </div>
          <div className="text-xs text-indigo-700">Skills Practiced</div>
        </div>
        <div className="p-3 bg-teal-50 rounded-lg">
          <div className="text-2xl font-bold text-teal-900">
            {data.total_conversations}
          </div>
          <div className="text-xs text-teal-700">Conversations</div>
        </div>
      </div>

      {/* Skills Breakdown */}
      {skillsArray.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-semibold text-secondary mb-2">Skills Practiced</div>
          <div className="space-y-2">
            {skillsArray.slice(0, 5).map(([skill, count]) => {
              const maxCount = Math.max(...skillsArray.map(s => s[1]));
              const percentage = (count / maxCount) * 100;
              return (
                <div key={skill} className="flex items-center gap-2">
                  <div className="w-32 text-xs truncate" style={{ color: 'var(--color-text-secondary)' }} title={skillLabels[skill] || skill}>
                    {skillLabels[skill] || skill}
                  </div>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
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
        </div>
      )}

      {/* Growth Trend */}
      {data.growth_trend && data.growth_trend.length > 0 && (
        <div className="border-t border-default pt-4">
          <div className="text-xs font-semibold text-secondary mb-2">Growth Over Time</div>
          <div className="bg-gray-50 p-2 rounded-lg">
            <div className="flex items-end gap-1.5 h-16 mb-1">
              {data.growth_trend.slice(-8).map((point, idx) => {
                const maxMentions = Math.max(...data.growth_trend.map(p => p.total_mentions));
                const height = maxMentions > 0 ? (point.total_mentions / maxMentions) * 100 : 0;
                const displayHeight = point.total_mentions > 0 ? Math.max(height, 10) : 2;

                return (
                  <div key={idx} className="flex-1">
                    <div
                      className="w-full bg-teal-400 hover:bg-teal-500 rounded-t transition-all duration-200 cursor-pointer relative group"
                      style={{ height: `${displayHeight}%` }}
                      title={`Week ${point.week}: ${point.skills_practiced} skills, ${point.total_mentions} mentions`}
                    >
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                        {point.skills_practiced} skills
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Topics Explored */}
      {data.topics_explored && data.topics_explored.length > 0 && (
        <div className="mt-4 pt-4 border-t border-default">
          <div className="text-xs font-semibold text-secondary mb-2">Recent Topics</div>
          <div className="flex flex-wrap gap-1">
            {data.topics_explored.slice(0, 6).map((topic, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full truncate max-w-[150px]"
                title={topic}
              >
                {topic}
              </span>
            ))}
            {data.topics_explored.length > 6 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                +{data.topics_explored.length - 6} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default memo(LearningProgressCard);
