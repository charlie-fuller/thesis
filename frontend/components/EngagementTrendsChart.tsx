'use client';

import { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import LoadingSpinner from './LoadingSpinner';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';

// Engagement level colors
const ENGAGEMENT_COLORS = {
  champion: '#22c55e',  // green-500
  supporter: '#14b8a6', // teal-500
  neutral: '#6b7280',   // gray-500
  skeptic: '#f97316',   // orange-500
  blocker: '#ef4444',   // red-500
};

interface EngagementTrend {
  date: string;
  champion: number;
  supporter: number;
  neutral: number;
  skeptic: number;
  blocker: number;
}

interface EngagementChange {
  stakeholder_id: string;
  name: string;
  previous_level: string;
  new_level: string;
  direction: 'up' | 'down' | 'same';
  change_date: string;
  reason: string;
}

export default function EngagementTrendsChart() {
  const [trends, setTrends] = useState<EngagementTrend[]>([]);
  const [changes, setChanges] = useState<EngagementChange[]>([]);
  const [days, setDays] = useState(90);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fetchData is stable
  }, [days]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [trendsData, changesData] = await Promise.all([
        apiGet<EngagementTrend[]>(`/api/stakeholders/engagement/trends?days=${days}`),
        apiGet<EngagementChange[]>('/api/stakeholders/engagement/changes?days=30')
      ]);
      setTrends(trendsData || []);
      setChanges(changesData || []);
    } catch (err) {
      logger.error('Error fetching engagement data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load engagement data');
      setTrends([]);
      setChanges([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    if (!confirm('Recalculate engagement levels for all stakeholders? This may take a moment.')) {
      return;
    }
    setRecalculating(true);
    try {
      const result = await apiPost<{
        message: string;
        total: number;
        changed: number;
        promotions: number;
        demotions: number;
      }>('/api/stakeholders/engagement/recalculate', {});
      alert(`Recalculation complete: ${result.changed} of ${result.total} stakeholders changed (${result.promotions} promotions, ${result.demotions} demotions)`);
      fetchData(); // Refresh data
    } catch (err) {
      logger.error('Recalculation failed:', err);
      alert(err instanceof Error ? err.message : 'Recalculation failed');
    } finally {
      setRecalculating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getLevelBadgeClass = (level: string) => {
    switch (level.toLowerCase()) {
      case 'champion':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
      case 'supporter':
        return 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300';
      case 'neutral':
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
      case 'skeptic':
        return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300';
      case 'blocker':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 dark:text-red-400 p-4">
        <p>{error}</p>
        <button
          onClick={fetchData}
          className="mt-2 text-sm text-brand hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Engagement Trends Chart */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-primary">
            Engagement Trends
          </h3>
          <div className="flex items-center gap-3">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-1.5 text-sm border border-default rounded-lg bg-card text-primary"
            >
              <option value={30}>Last 30 days</option>
              <option value={60}>Last 60 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            <button
              onClick={handleRecalculate}
              disabled={recalculating}
              className="px-3 py-1.5 text-sm border border-default rounded-lg bg-card text-secondary hover:text-primary hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50"
              title="Manually trigger engagement recalculation"
            >
              {recalculating ? 'Calculating...' : 'Recalculate'}
            </button>
          </div>
        </div>

        {trends.length === 0 ? (
          <div className="text-center text-muted py-12">
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p>No engagement history yet</p>
            <p className="text-sm mt-1">Data will appear after the weekly calculation runs</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                className="text-xs"
                tick={{ fill: 'currentColor' }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: 'currentColor' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--color-card)',
                  borderColor: 'var(--color-border)',
                  borderRadius: '0.5rem',
                }}
                labelFormatter={formatDate}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="champion"
                stackId="1"
                stroke={ENGAGEMENT_COLORS.champion}
                fill={ENGAGEMENT_COLORS.champion}
                fillOpacity={0.6}
                name="Champion"
              />
              <Area
                type="monotone"
                dataKey="supporter"
                stackId="1"
                stroke={ENGAGEMENT_COLORS.supporter}
                fill={ENGAGEMENT_COLORS.supporter}
                fillOpacity={0.6}
                name="Supporter"
              />
              <Area
                type="monotone"
                dataKey="neutral"
                stackId="1"
                stroke={ENGAGEMENT_COLORS.neutral}
                fill={ENGAGEMENT_COLORS.neutral}
                fillOpacity={0.6}
                name="Neutral"
              />
              <Area
                type="monotone"
                dataKey="skeptic"
                stackId="1"
                stroke={ENGAGEMENT_COLORS.skeptic}
                fill={ENGAGEMENT_COLORS.skeptic}
                fillOpacity={0.6}
                name="Skeptic"
              />
              <Area
                type="monotone"
                dataKey="blocker"
                stackId="1"
                stroke={ENGAGEMENT_COLORS.blocker}
                fill={ENGAGEMENT_COLORS.blocker}
                fillOpacity={0.6}
                name="Blocker"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Recent Engagement Changes */}
      {changes.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-primary mb-4">
            Recent Engagement Changes
          </h3>
          <div className="space-y-3">
            {changes.slice(0, 10).map((change, idx) => (
              <div
                key={`${change.stakeholder_id}-${idx}`}
                className="flex items-center gap-3 p-3 bg-subtle rounded-lg"
              >
                {/* Direction indicator */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  change.direction === 'up'
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                    : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                }`}>
                  {change.direction === 'up' ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  )}
                </div>

                {/* Name and level change */}
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-primary truncate">
                    {change.name}
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className={`px-2 py-0.5 rounded text-xs capitalize ${getLevelBadgeClass(change.previous_level)}`}>
                      {change.previous_level}
                    </span>
                    <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                    <span className={`px-2 py-0.5 rounded text-xs capitalize ${getLevelBadgeClass(change.new_level)}`}>
                      {change.new_level}
                    </span>
                  </div>
                </div>

                {/* Reason tooltip */}
                <div className="flex-shrink-0" title={change.reason}>
                  <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>

                {/* Date */}
                <div className="flex-shrink-0 text-xs text-muted">
                  {formatDate(change.change_date)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
