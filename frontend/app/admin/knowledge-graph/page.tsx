'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from '@/components/LoadingSpinner';
import GraphVisualization, { NODE_COLORS } from '@/components/admin/GraphVisualization';
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

interface SelectedNode {
  id: string;
  label: string;
  name: string;
  properties: Record<string, unknown>;
  [key: string]: unknown;
}

export default function KnowledgeGraphPage() {
  const { user, session, loading: authLoading } = useAuth();
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [health, setHealth] = useState<GraphHealth | null>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [visibleNodeTypes, setVisibleNodeTypes] = useState<Set<string>>(new Set());
  const [allNodeTypes, setAllNodeTypes] = useState<string[]>([]);

  // Fetch data on mount
  useEffect(() => {
    if (authLoading || !user || !session) return;
    fetchData();
  }, [authLoading, user, session]);

  const fetchData = async () => {
    try {
      setLoading(true);

      const healthData = await apiGet<GraphHealth>('/api/graph/health').catch(() => ({
        status: 'unhealthy' as const,
        error: 'Could not connect to graph service'
      }));
      setHealth(healthData);

      if (healthData.status === 'healthy') {
        const [statsData, schedulerData] = await Promise.all([
          apiGet<GraphStats>('/api/graph/stats').catch(() => null),
          apiGet<SchedulerStatus>('/api/graph/sync/scheduler-status').catch(() => null)
        ]);
        setStats(statsData);
        setSchedulerStatus(schedulerData);

        // Initialize visible node types from stats
        if (statsData?.nodes.by_label) {
          const types = Object.keys(statsData.nodes.by_label);
          setAllNodeTypes(types);
          setVisibleNodeTypes(new Set(types));
        }
      }
    } catch (err) {
      logger.error('Error fetching graph data:', err);
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async () => {
    try {
      setSyncing(true);
      setSyncMessage(null);

      const result = await apiPost<{ success: boolean; message: string }>(
        '/api/graph/sync/trigger',
        {}
      );

      if (result.success) {
        setSyncMessage('Sync started. Refreshing in 10 seconds...');
        setTimeout(() => {
          fetchData();
          setSyncMessage(null);
        }, 10000);
      }
    } catch (err) {
      logger.error('Error triggering sync:', err);
      setSyncMessage('Failed to start sync');
    } finally {
      setSyncing(false);
    }
  };

  const toggleNodeType = (type: string) => {
    setVisibleNodeTypes(prev => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const toggleAllNodeTypes = () => {
    if (visibleNodeTypes.size === allNodeTypes.length) {
      setVisibleNodeTypes(new Set());
    } else {
      setVisibleNodeTypes(new Set(allNodeTypes));
    }
  };

  const formatNextRun = (isoString: string | null): string => {
    if (!isoString) return 'Not scheduled';
    try {
      const date = new Date(isoString);
      return date.toLocaleString();
    } catch {
      return 'Unknown';
    }
  };

  const getTopItems = (record: Record<string, number>, n: number = 10) => {
    return Object.entries(record)
      .sort((a, b) => b[1] - a[1])
      .slice(0, n);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-secondary mt-4">Loading Knowledge Graph...</p>
        </div>
      </div>
    );
  }

  if (health?.status === 'unhealthy') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/" className="text-secondary hover:text-primary text-sm mb-2 inline-block">
              &larr; Back to Dashboard
            </Link>
            <h1 className="text-2xl font-semibold text-primary">Knowledge Graph</h1>
          </div>
        </div>
        <div className="card p-8 text-center">
          <div className="text-red-400 mb-4">Graph service unavailable</div>
          <p className="text-secondary text-sm mb-4">{health.error}</p>
          <button onClick={fetchData} className="btn-secondary">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-secondary hover:text-primary text-sm mb-2 inline-block">
            &larr; Back to Dashboard
          </Link>
          <h1 className="text-2xl font-semibold text-primary">Knowledge Graph</h1>
          <p className="text-secondary text-sm mt-1">
            Interactive visualization of your platform data connections
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              <span className="text-secondary">Connected</span>
            </div>
            <div className="text-xs text-muted">
              Next sync: {formatNextRun(schedulerStatus?.jobs[0]?.next_run_time || null)}
            </div>
          </div>
          <button
            onClick={triggerSync}
            disabled={syncing}
            className="btn-primary disabled:opacity-50"
          >
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
        </div>
      </div>

      {syncMessage && (
        <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg px-4 py-3 text-sm text-purple-300">
          {syncMessage}
        </div>
      )}

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-4 text-center">
            <div className="text-3xl font-bold text-purple-400">
              {stats.nodes.total.toLocaleString()}
            </div>
            <div className="text-sm text-secondary">Total Nodes</div>
          </div>
          <div className="card p-4 text-center">
            <div className="text-3xl font-bold text-blue-400">
              {stats.relationships.total.toLocaleString()}
            </div>
            <div className="text-sm text-secondary">Relationships</div>
          </div>
          <div className="card p-4 text-center">
            <div className="text-3xl font-bold text-green-400">
              {Object.keys(stats.nodes.by_label).length}
            </div>
            <div className="text-sm text-secondary">Node Types</div>
          </div>
          <div className="card p-4 text-center">
            <div className="text-3xl font-bold text-amber-400">
              {Object.keys(stats.relationships.by_type).length}
            </div>
            <div className="text-sm text-secondary">Relationship Types</div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar - Filters */}
        <div className="lg:col-span-1 space-y-4">
          {/* Node Type Filters */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-primary">Node Types</h3>
              <button
                onClick={toggleAllNodeTypes}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                {visibleNodeTypes.size === allNodeTypes.length ? 'Hide All' : 'Show All'}
              </button>
            </div>
            <div className="space-y-2">
              {allNodeTypes.map(type => (
                <label key={type} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={visibleNodeTypes.has(type)}
                    onChange={() => toggleNodeType(type)}
                    className="rounded border-border bg-input"
                  />
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: NODE_COLORS[type] || '#6b7280' }}
                  />
                  <span className="text-sm text-primary flex-1">{type}</span>
                  <span className="text-xs text-secondary">
                    {stats?.nodes.by_label[type] || 0}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Relationship Types */}
          {stats && Object.keys(stats.relationships.by_type).length > 0 && (
            <div className="card p-4">
              <h3 className="font-medium text-primary mb-3">Relationship Types</h3>
              <div className="space-y-1">
                {getTopItems(stats.relationships.by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-sm">
                    <span className="text-secondary font-mono text-xs">{type}</span>
                    <span className="text-muted">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Graph Visualization */}
        <div className="lg:col-span-2 h-[600px]">
          <GraphVisualization
            onNodeSelect={setSelectedNode}
            selectedNode={selectedNode}
            visibleNodeTypes={visibleNodeTypes.size > 0 ? visibleNodeTypes : undefined}
          />
        </div>

        {/* Right Sidebar - Node Details */}
        <div className="lg:col-span-1">
          <div className="card p-4 h-[600px] overflow-y-auto">
            {selectedNode ? (
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: NODE_COLORS[selectedNode.label] || '#6b7280' }}
                  />
                  <span className="font-medium text-primary">{selectedNode.name}</span>
                </div>
                <div className="text-xs text-purple-400 mb-4">{selectedNode.label}</div>

                <h4 className="text-sm font-medium text-secondary mb-2">Properties</h4>
                <div className="space-y-2">
                  {Object.entries(selectedNode.properties)
                    .filter(([key]) => !key.startsWith('_') && key !== 'id')
                    .slice(0, 15)
                    .map(([key, value]) => (
                      <div key={key} className="text-sm">
                        <div className="text-muted text-xs">{key}</div>
                        <div className="text-primary truncate" title={String(value)}>
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-center">
                <div>
                  <div className="text-4xl mb-4 opacity-20">🔍</div>
                  <p className="text-secondary text-sm">Click a node to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="card p-4">
        <h3 className="text-sm font-medium text-secondary mb-3">Legend</h3>
        <div className="flex flex-wrap gap-4">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-secondary">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
