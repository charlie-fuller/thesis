'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from '@/components/LoadingSpinner';
import GraphVisualization, { NODE_COLORS } from '@/components/admin/GraphVisualization';
import { useAuth } from '@/contexts/AuthContext';
import { Database, Network, HelpCircle } from 'lucide-react';

type TabType = 'data' | 'visualization' | 'what-is-this';

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
  const [activeTab, setActiveTab] = useState<TabType>('visualization');

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

      {/* Tab Navigation */}
      <div className="border-b border-border">
        <nav className="-mb-px flex gap-4">
          <button
            onClick={() => setActiveTab('data')}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'data'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-secondary hover:text-primary hover:border-border'
            }`}
          >
            <Database className="w-4 h-4" />
            Data
          </button>
          <button
            onClick={() => setActiveTab('visualization')}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'visualization'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-secondary hover:text-primary hover:border-border'
            }`}
          >
            <Network className="w-4 h-4" />
            Visualization
          </button>
          <button
            onClick={() => setActiveTab('what-is-this')}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'what-is-this'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-secondary hover:text-primary hover:border-border'
            }`}
          >
            <HelpCircle className="w-4 h-4" />
            What is this?
          </button>
        </nav>
      </div>

      {/* Data Tab */}
      {activeTab === 'data' && (
        <div className="space-y-6">
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

          {/* Data Tables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Node Types Breakdown */}
            <div className="card p-6">
              <h3 className="font-medium text-primary mb-4">Nodes by Type</h3>
              <div className="space-y-2">
                {stats && Object.entries(stats.nodes.by_label)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: NODE_COLORS[type] || '#6b7280' }}
                        />
                        <span className="text-sm text-primary">{type}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-24 bg-surface rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full bg-purple-500/50"
                            style={{ width: `${(count / (stats?.nodes.total || 1)) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-secondary w-12 text-right">
                          {count.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Relationship Types Breakdown */}
            <div className="card p-6">
              <h3 className="font-medium text-primary mb-4">Relationships by Type</h3>
              <div className="space-y-2">
                {stats && Object.entries(stats.relationships.by_type)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <span className="text-sm text-primary font-mono">{type}</span>
                      <div className="flex items-center gap-3">
                        <div className="w-24 bg-surface rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full bg-blue-500/50"
                            style={{ width: `${(count / (stats?.relationships.total || 1)) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-secondary w-12 text-right">
                          {count.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Visualization Tab */}
      {activeTab === 'visualization' && (
        <div className="space-y-6">
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
                      <div className="text-4xl mb-4 opacity-20">
                        <svg className="w-10 h-10 mx-auto text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
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
      )}

      {/* What is this? Tab */}
      {activeTab === 'what-is-this' && (
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="card p-8">
            <h2 className="text-xl font-semibold text-primary mb-4">What is a Knowledge Graph?</h2>
            <p className="text-secondary leading-relaxed">
              A knowledge graph is a structured representation of information that captures
              entities (nodes) and the relationships between them (edges). Unlike traditional
              databases that store data in isolated tables, a knowledge graph connects
              information in a way that mirrors how concepts relate in the real world.
            </p>
          </div>

          <div className="card p-8">
            <h2 className="text-xl font-semibold text-primary mb-4">Why is it Important?</h2>
            <div className="space-y-4 text-secondary leading-relaxed">
              <p>
                Knowledge graphs enable AI systems to understand context and connections
                that would otherwise be invisible. When your agents analyze documents,
                stakeholders, projects, and meetings, the knowledge graph captures how
                all these elements relate to each other.
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><strong className="text-primary">Contextual Understanding:</strong> Agents can see that a document was discussed in a meeting, relates to a project, and involves specific stakeholders</li>
                <li><strong className="text-primary">Discovery:</strong> Surface hidden connections between people, topics, and initiatives across your organization</li>
                <li><strong className="text-primary">Memory:</strong> Maintain persistent knowledge that grows over time, not just single conversations</li>
              </ul>
            </div>
          </div>

          <div className="card p-8">
            <h2 className="text-xl font-semibold text-primary mb-4">How Does it Add Value?</h2>
            <div className="grid gap-4">
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-purple-400 text-lg">1</span>
                </div>
                <div>
                  <h3 className="font-medium text-primary">Smarter Agent Responses</h3>
                  <p className="text-secondary text-sm">Agents can pull in relevant context from connected entities, providing more informed and nuanced answers.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-blue-400 text-lg">2</span>
                </div>
                <div>
                  <h3 className="font-medium text-primary">Cross-Domain Insights</h3>
                  <p className="text-secondary text-sm">Discover connections between stakeholders, documents, and projects that span different areas of your organization.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-green-400 text-lg">3</span>
                </div>
                <div>
                  <h3 className="font-medium text-primary">Institutional Knowledge</h3>
                  <p className="text-secondary text-sm">Build a growing repository of organizational knowledge that persists beyond individual conversations or team members.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-amber-400 text-lg">4</span>
                </div>
                <div>
                  <h3 className="font-medium text-primary">Impact Analysis</h3>
                  <p className="text-secondary text-sm">Understand how changes to one area might affect connected stakeholders, projects, or initiatives.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card p-8">
            <h2 className="text-xl font-semibold text-primary mb-4">How is it Used in Thesis?</h2>
            <div className="space-y-4 text-secondary leading-relaxed">
              <p>
                The knowledge graph in Thesis automatically syncs data from across the platform:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li><strong className="text-primary">Documents</strong> from your Knowledge Base with their topics and categories</li>
                <li><strong className="text-primary">Stakeholders</strong> and their relationships to projects and initiatives</li>
                <li><strong className="text-primary">Projects</strong> and their connected documents and team members</li>
                <li><strong className="text-primary">Meeting Notes</strong> linked to attendees, action items, and discussed topics</li>
                <li><strong className="text-primary">Tasks</strong> connected to their assignees and related projects</li>
              </ul>
              <p className="mt-4">
                When agents process your queries, they can traverse these connections to provide
                comprehensive answers that consider the full context of your organization&apos;s
                knowledge and relationships.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
