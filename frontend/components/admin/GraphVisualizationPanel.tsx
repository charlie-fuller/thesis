'use client';

import { useState, useEffect } from 'react';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from '../LoadingSpinner';
import GraphVisualization, { NODE_COLORS } from './GraphVisualization';
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

interface SelectedNode {
  id: string;
  label: string;
  name: string;
  properties: Record<string, unknown>;
  [key: string]: unknown;
}

export default function GraphVisualizationPanel() {
  const { user, session, loading: authLoading } = useAuth();
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [visibleNodeTypes, setVisibleNodeTypes] = useState<Set<string>>(new Set());
  const [allNodeTypes, setAllNodeTypes] = useState<string[]>([]);

  useEffect(() => {
    if (authLoading || !user || !session) return;
    fetchStats();
  }, [authLoading, user, session]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const statsData = await apiGet<GraphStats>('/api/graph/stats').catch(() => null);
      setStats(statsData);

      if (statsData?.nodes.by_label) {
        const types = Object.keys(statsData.nodes.by_label);
        setAllNodeTypes(types);
        setVisibleNodeTypes(new Set(types));
      }
    } catch (err) {
      logger.error('Error fetching graph stats:', err);
    } finally {
      setLoading(false);
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

  const getTopItems = (record: Record<string, number>, n: number = 8) => {
    return Object.entries(record)
      .sort((a, b) => b[1] - a[1])
      .slice(0, n);
  };

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center h-[500px]">
          <div className="text-center">
            <LoadingSpinner size="lg" />
            <p className="text-secondary mt-4">Loading graph...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-4 gap-3">
          <div className="card p-3 text-center">
            <div className="text-2xl font-bold text-purple-400">
              {stats.nodes.total.toLocaleString()}
            </div>
            <div className="text-xs text-secondary">Nodes</div>
          </div>
          <div className="card p-3 text-center">
            <div className="text-2xl font-bold text-blue-400">
              {stats.relationships.total.toLocaleString()}
            </div>
            <div className="text-xs text-secondary">Relationships</div>
          </div>
          <div className="card p-3 text-center">
            <div className="text-2xl font-bold text-green-400">
              {Object.keys(stats.nodes.by_label).length}
            </div>
            <div className="text-xs text-secondary">Node Types</div>
          </div>
          <div className="card p-3 text-center">
            <div className="text-2xl font-bold text-amber-400">
              {Object.keys(stats.relationships.by_type).length}
            </div>
            <div className="text-xs text-secondary">Rel Types</div>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Left Sidebar - Filters */}
        <div className="lg:col-span-1 space-y-3">
          {/* Node Type Filters */}
          <div className="card p-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-primary">Node Types</h3>
              <button
                onClick={toggleAllNodeTypes}
                className="text-xs text-purple-400 hover:text-purple-300"
              >
                {visibleNodeTypes.size === allNodeTypes.length ? 'Hide All' : 'Show All'}
              </button>
            </div>
            <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
              {allNodeTypes.map(type => (
                <label key={type} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={visibleNodeTypes.has(type)}
                    onChange={() => toggleNodeType(type)}
                    className="rounded border-border bg-input w-3.5 h-3.5"
                  />
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: NODE_COLORS[type] || '#6b7280' }}
                  />
                  <span className="text-xs text-primary flex-1 truncate">{type}</span>
                  <span className="text-xs text-muted">
                    {stats?.nodes.by_label[type] || 0}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Relationship Types */}
          {stats && Object.keys(stats.relationships.by_type).length > 0 && (
            <div className="card p-3">
              <h3 className="text-sm font-medium text-primary mb-2">Relationships</h3>
              <div className="space-y-1 max-h-[150px] overflow-y-auto">
                {getTopItems(stats.relationships.by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-xs">
                    <span className="text-secondary font-mono truncate flex-1">{type}</span>
                    <span className="text-muted ml-2">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Graph Visualization */}
        <div className="lg:col-span-2 h-[500px]">
          <GraphVisualization
            onNodeSelect={setSelectedNode}
            selectedNode={selectedNode}
            visibleNodeTypes={visibleNodeTypes.size > 0 ? visibleNodeTypes : undefined}
          />
        </div>

        {/* Right Sidebar - Node Details */}
        <div className="lg:col-span-1">
          <div className="card p-3 h-[500px] overflow-y-auto">
            {selectedNode ? (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: NODE_COLORS[selectedNode.label] || '#6b7280' }}
                  />
                  <span className="text-sm font-medium text-primary truncate">{selectedNode.name}</span>
                </div>
                <div className="text-xs text-purple-400 mb-3">{selectedNode.label}</div>

                <h4 className="text-xs font-medium text-secondary mb-2">Properties</h4>
                <div className="space-y-2">
                  {Object.entries(selectedNode.properties)
                    .filter(([key]) => !key.startsWith('_') && key !== 'id')
                    .slice(0, 10)
                    .map(([key, value]) => (
                      <div key={key} className="text-xs">
                        <div className="text-muted">{key}</div>
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
                  <div className="text-3xl mb-3 opacity-20">🔍</div>
                  <p className="text-secondary text-xs">Click a node to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="card p-3">
        <h3 className="text-xs font-medium text-secondary mb-2">Legend</h3>
        <div className="flex flex-wrap gap-3">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full"
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
