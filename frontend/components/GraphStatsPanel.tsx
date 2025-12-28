'use client';

import { useState, useEffect } from 'react';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from './LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';

interface GraphStats {
  nodes: {
    total: number;
    by_label: Record<string, number>;
  };
  relationships: {
    total: number;
    by_type: Record<string, number>;
  };
}

interface GraphHealth {
  status: 'healthy' | 'unhealthy';
  connected?: boolean;
  error?: string;
}

interface SchedulerStatus {
  running: boolean;
  jobs: Array<{
    id: string;
    name: string;
    next_run_time: string | null;
  }>;
}

export default function GraphStatsPanel() {
  const { user, session, loading: authLoading } = useAuth();
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [health, setHealth] = useState<GraphHealth | null>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  useEffect(() => {
    // Wait for auth to complete and session to be available before fetching data
    // This prevents 401 errors from race conditions during auth initialization
    if (authLoading || !user || !session) {
      return;
    }
    fetchGraphData();
  }, [authLoading, user, session]);

  const fetchGraphData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch health first
      const healthData = await apiGet<GraphHealth>('/api/graph/health').catch(() => ({
        status: 'unhealthy' as const,
        error: 'Could not connect to graph service'
      }));
      setHealth(healthData);

      // If healthy, fetch stats and scheduler status
      if (healthData.status === 'healthy') {
        const [statsData, schedulerData] = await Promise.all([
          apiGet<GraphStats>('/api/graph/stats').catch(() => null),
          apiGet<SchedulerStatus>('/api/graph/sync/scheduler-status').catch(() => null)
        ]);
        setStats(statsData);
        setSchedulerStatus(schedulerData);
      }
    } catch (err) {
      logger.error('Error fetching graph data:', err);
      setError('Failed to load graph statistics');
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async () => {
    try {
      setSyncing(true);
      setSyncMessage(null);

      const result = await apiPost<{ success: boolean; status: string; message: string }>(
        '/api/graph/sync/trigger',
        {}
      );

      if (result.success) {
        setSyncMessage('Sync started. Refreshing in 5 seconds...');
        // Refresh data after a delay to allow sync to complete
        setTimeout(() => {
          fetchGraphData();
          setSyncMessage(null);
        }, 5000);
      }
    } catch (err) {
      logger.error('Error triggering sync:', err);
      setSyncMessage('Failed to start sync');
    } finally {
      setSyncing(false);
    }
  };

  // Helper to get top N items from a record
  const getTopItems = (record: Record<string, number>, n: number = 5) => {
    return Object.entries(record)
      .sort((a, b) => b[1] - a[1])
      .slice(0, n);
  };

  // Format next run time
  const formatNextRun = (isoString: string | null): string => {
    if (!isoString) return 'Not scheduled';
    try {
      const date = new Date(isoString);
      return date.toLocaleString();
    } catch {
      return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-primary mb-4">Knowledge Graph</h2>
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error || health?.status === 'unhealthy') {
    return (
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-primary mb-4">Knowledge Graph</h2>
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
          <div className="text-red-600 dark:text-red-400 font-medium">
            {health?.error || error || 'Graph service unavailable'}
          </div>
          <button
            onClick={fetchGraphData}
            className="mt-3 text-sm text-red-500 hover:underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-primary">Knowledge Graph</h2>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500"></span>
          <span className="text-xs text-secondary">Connected</span>
        </div>
      </div>

      {stats ? (
        <>
          {/* Node Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-hover rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-purple-400">
                {stats.nodes.total.toLocaleString()}
              </div>
              <div className="text-sm text-secondary">Total Nodes</div>
            </div>
            <div className="bg-hover rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-blue-400">
                {stats.relationships.total.toLocaleString()}
              </div>
              <div className="text-sm text-secondary">Relationships</div>
            </div>
          </div>

          {/* Node Types */}
          <div className="mb-4">
            <h3 className="text-sm font-medium text-secondary mb-2">Top Node Types</h3>
            <div className="space-y-1">
              {getTopItems(stats.nodes.by_label).map(([label, count]) => (
                <div key={label} className="flex items-center justify-between text-sm">
                  <span className="text-primary">{label}</span>
                  <span className="text-secondary">{count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Relationship Types */}
          {Object.keys(stats.relationships.by_type).length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-secondary mb-2">Top Relationships</h3>
              <div className="space-y-1">
                {getTopItems(stats.relationships.by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-sm">
                    <span className="text-primary font-mono text-xs">{type}</span>
                    <span className="text-secondary">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sync Controls */}
          <div className="border-t border-border pt-4 mt-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-secondary">
                {schedulerStatus?.running ? (
                  <>
                    Next sync: {formatNextRun(schedulerStatus.jobs[0]?.next_run_time || null)}
                  </>
                ) : (
                  'Scheduler not running'
                )}
              </div>
              <button
                onClick={triggerSync}
                disabled={syncing}
                className="text-xs px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {syncing ? 'Syncing...' : 'Sync Now'}
              </button>
            </div>
            {syncMessage && (
              <div className="mt-2 text-xs text-center text-secondary">
                {syncMessage}
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="text-center py-4">
          <div className="text-secondary mb-4">No graph statistics available</div>
          <p className="text-xs text-secondary mb-4">
            The graph needs to be populated with data from the platform.
          </p>
          <button
            onClick={triggerSync}
            disabled={syncing}
            className="text-sm px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {syncing ? 'Syncing...' : 'Sync Data to Graph'}
          </button>
          {syncMessage && (
            <div className="mt-2 text-xs text-secondary">
              {syncMessage}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
