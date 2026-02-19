'use client';

import { useState, useEffect, useCallback } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, Copy, Check } from 'lucide-react';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from './LoadingSpinner';
import { AgentIcon } from './AgentIcon';

interface AgentCompliance {
  agent: string;
  messages: number;
  avg_score: number;
  level: string;
}

interface PrincipleStats {
  principle: string;
  hit_count: number;
  total_messages: number;
  hit_rate: number;
}

interface DriftAlert {
  agent: string;
  principle: string;
  hit_rate: number;
  messages: number;
}

interface SourceStats {
  messages: number;
  avg_score: number;
}

interface FlaggedItem {
  id: string;
  source: string;
  source_id: string;
  agent: string;
  score: number;
  level: string;
  signals: string[];
  gaps: string[];
  why_flagged: string;
  content_preview: string;
  created_at: string;
  recommendation: string;
}

interface FlaggedResponse {
  items: FlaggedItem[];
  total: number;
}

interface ComplianceData {
  period_days: number;
  total_scored_messages: number;
  by_agent: Record<string, AgentCompliance>;
  by_principle: Record<string, PrincipleStats>;
  drift_alerts: DriftAlert[];
  level_distribution: {
    aligned: number;
    drifting: number;
    misaligned: number;
  };
  by_source: Record<string, SourceStats>;
}

type TimeRange = 7 | 30 | 90;

function getLevelColor(level: string) {
  switch (level) {
    case 'aligned':
      return 'text-teal-400 bg-teal-500/20';
    case 'drifting':
      return 'text-amber-400 bg-amber-500/20';
    case 'misaligned':
      return 'text-red-400 bg-red-500/20';
    default:
      return 'text-secondary bg-hover';
  }
}

function formatPrinciple(id: string): string {
  const parts = id.split('_');
  if (parts.length < 2) return id;
  return parts.slice(1).join(' ').replace(/^\w/, (c) => c.toUpperCase());
}

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function buildCopyText(item: FlaggedItem): string {
  const lines = [
    `Agent: ${item.agent}`,
    `Score: ${(item.score * 100).toFixed(0)}% (${item.level})`,
    `Source: ${item.source === 'chat' ? 'Chat' : 'Meeting Room'}`,
    `Time: ${new Date(item.created_at).toLocaleString()}`,
    `Why flagged: ${item.why_flagged}`,
    `Recommendation: ${item.recommendation}`,
    `Preview: ${item.content_preview}`,
  ];
  return lines.join('\n');
}

function FlaggedItemsPanel({
  level,
  count,
  days,
}: {
  level: 'drifting' | 'misaligned';
  count: number;
  days: TimeRange;
}) {
  const [expanded, setExpanded] = useState(false);
  const [items, setItems] = useState<FlaggedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const isDrifting = level === 'drifting';
  const borderColor = isDrifting ? 'border-amber-500/30' : 'border-red-500/30';
  const bgColor = isDrifting ? 'bg-amber-500/5' : 'bg-red-500/5';
  const headerText = isDrifting ? 'text-amber-400' : 'text-red-400';
  const badgeBg = isDrifting ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400';
  const label = isDrifting ? 'Drifting Items' : 'Misaligned Items';

  const handleToggle = useCallback(async () => {
    const opening = !expanded;
    setExpanded(opening);
    if (opening && !loaded) {
      setLoading(true);
      try {
        const result = await apiGet<FlaggedResponse>(
          `/api/admin/analytics/manifesto-compliance/flagged?days=${days}&level=${level}`
        );
        setItems(result.items);
        setLoaded(true);
      } catch (err) {
        logger.error('Failed to fetch flagged items', err);
      } finally {
        setLoading(false);
      }
    }
  }, [expanded, loaded, days, level]);

  // Reset loaded state when days change
  useEffect(() => {
    setLoaded(false);
    setItems([]);
    if (expanded) {
      setExpanded(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const handleCopy = useCallback((item: FlaggedItem) => {
    navigator.clipboard.writeText(buildCopyText(item));
    setCopiedId(item.id);
    setTimeout(() => setCopiedId(null), 2000);
  }, []);

  if (count === 0) return null;

  return (
    <div className={`card border ${borderColor} ${bgColor}`}>
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-2">
          {expanded ? (
            <ChevronDown className={`w-4 h-4 ${headerText}`} />
          ) : (
            <ChevronRight className={`w-4 h-4 ${headerText}`} />
          )}
          <span className={`text-sm font-medium ${headerText}`}>{label}</span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badgeBg}`}>
            {count}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {loading && (
            <div className="flex justify-center py-4">
              <LoadingSpinner size="sm" />
            </div>
          )}

          {!loading && items.length === 0 && loaded && (
            <p className="text-sm text-muted py-2">No items found.</p>
          )}

          {items.map((item) => {
            const link =
              item.source === 'chat'
                ? `/chat?id=${item.source_id}`
                : `/meeting-room/${item.source_id}`;
            return (
              <div
                key={item.id}
                className="p-3 rounded-lg bg-card border border-default space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AgentIcon name={item.agent} size="sm" />
                    <span className="text-sm font-medium text-primary capitalize">
                      {item.agent}
                    </span>
                    <span className="text-xs text-muted">
                      {(item.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted">
                      {relativeTime(item.created_at)}
                    </span>
                    <button
                      onClick={() => handleCopy(item)}
                      className="p-1 rounded hover:bg-hover text-muted hover:text-primary transition-colors"
                      title="Copy details"
                    >
                      {copiedId === item.id ? (
                        <Check className="w-3.5 h-3.5 text-teal-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                    <a
                      href={link}
                      className="p-1 rounded hover:bg-hover text-muted hover:text-primary transition-colors"
                      title="Go to source"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>

                <p className="text-xs text-secondary leading-relaxed">
                  {item.content_preview}
                </p>

                <p className="text-xs text-muted">
                  <span className="font-medium text-secondary">Why flagged: </span>
                  {item.why_flagged}
                </p>

                <p className="text-xs text-muted">
                  <span className="font-medium text-secondary">Recommendation: </span>
                  {item.recommendation}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function ManifestoCompliancePanel() {
  const [data, setData] = useState<ComplianceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState<TimeRange>(30);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const result = await apiGet<ComplianceData>(
          `/api/admin/analytics/manifesto-compliance?days=${days}`
        );
        setData(result);
      } catch (err) {
        logger.error('Failed to fetch compliance data', err);
        setError('Failed to load compliance data');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-6">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const total = data.total_scored_messages;
  const { aligned, drifting, misaligned } = data.level_distribution;
  const alignedPct = total > 0 ? Math.round((aligned / total) * 100) : 0;
  const driftingPct = total > 0 ? Math.round((drifting / total) * 100) : 0;
  const misalignedPct = total > 0 ? Math.round((misaligned / total) * 100) : 0;

  const agents = Object.entries(data.by_agent)
    .map(([name, a]) => ({ ...a, agent: name }))
    .filter((a) => a.agent)
    .sort((a, b) => b.messages - a.messages);

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-primary">Manifesto Compliance</h2>
        <div className="flex gap-1 bg-hover rounded-lg p-1">
          {([7, 30, 90] as TimeRange[]).map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                days === d
                  ? 'bg-card text-primary shadow-sm'
                  : 'text-muted hover:text-primary'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-sm text-secondary">Total Scored</p>
          <p className="text-2xl font-bold text-primary">{total}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary">Aligned</p>
          <p className="text-2xl font-bold text-teal-400">{alignedPct}%</p>
          <p className="text-xs text-muted">{aligned} messages</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary">Drifting</p>
          <p className="text-2xl font-bold text-amber-400">{driftingPct}%</p>
          <p className="text-xs text-muted">{drifting} messages</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary">Misaligned</p>
          <p className="text-2xl font-bold text-red-400">{misalignedPct}%</p>
          <p className="text-xs text-muted">{misaligned} messages</p>
        </div>
      </div>

      {/* Level Distribution Bar */}
      {total > 0 && (
        <div className="card p-4">
          <p className="text-sm text-secondary mb-2">Level Distribution</p>
          <div className="flex h-4 rounded-full overflow-hidden bg-hover">
            {alignedPct > 0 && (
              <div
                className="bg-teal-500 transition-all"
                style={{ width: `${alignedPct}%` }}
                title={`Aligned: ${alignedPct}%`}
              />
            )}
            {driftingPct > 0 && (
              <div
                className="bg-amber-500 transition-all"
                style={{ width: `${driftingPct}%` }}
                title={`Drifting: ${driftingPct}%`}
              />
            )}
            {misalignedPct > 0 && (
              <div
                className="bg-red-500 transition-all"
                style={{ width: `${misalignedPct}%` }}
                title={`Misaligned: ${misalignedPct}%`}
              />
            )}
          </div>
          <div className="flex gap-4 mt-2 text-xs text-muted">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-teal-500" /> Aligned
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-500" /> Drifting
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" /> Misaligned
            </span>
          </div>
        </div>
      )}

      {/* Drill-Down Panels */}
      {drifting > 0 && (
        <FlaggedItemsPanel level="drifting" count={drifting} days={days} />
      )}
      {misaligned > 0 && (
        <FlaggedItemsPanel level="misaligned" count={misaligned} days={days} />
      )}

      {/* Per-Agent Table */}
      {agents.length > 0 && (
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-default">
            <h3 className="text-sm font-medium text-primary">Per-Agent Compliance</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-default text-left text-muted">
                  <th className="px-4 py-3 font-medium">Agent</th>
                  <th className="px-4 py-3 font-medium text-right">Messages</th>
                  <th className="px-4 py-3 font-medium text-right">Avg Score</th>
                  <th className="px-4 py-3 font-medium text-right">Level</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((agent) => (
                  <tr key={agent.agent} className="border-b border-default last:border-0">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <AgentIcon name={agent.agent} size="sm" />
                        <span className="text-primary capitalize">{agent.agent}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right text-secondary">{agent.messages}</td>
                    <td className="px-4 py-3 text-right text-secondary">
                      {(agent.avg_score * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getLevelColor(agent.level)}`}>
                        {agent.level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Drift Alerts */}
      {data.drift_alerts.length > 0 && (
        <div className="card p-4">
          <h3 className="text-sm font-medium text-primary mb-3">Drift Alerts</h3>
          <div className="space-y-2">
            {data.drift_alerts.map((alert, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-2">
                  <AgentIcon name={alert.agent} size="sm" />
                  <div>
                    <span className="text-primary capitalize">{alert.agent}</span>
                    <span className="text-muted mx-2">--</span>
                    <span className="text-secondary">{alert.principle.replace(/_/g, ' ')}</span>
                  </div>
                </div>
                <div className="text-right text-sm">
                  <span className="text-amber-400 font-medium">
                    {(alert.hit_rate * 100).toFixed(0)}% hit rate
                  </span>
                  <span className="text-muted ml-2">({alert.messages} msgs)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Source Breakdown */}
      {Object.keys(data.by_source).length > 0 && (
        <div className="card p-4">
          <h3 className="text-sm font-medium text-primary mb-3">Source Breakdown</h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(data.by_source).map(([source, stats]) => (
              <div key={source} className="p-3 rounded-lg bg-hover">
                <p className="text-sm font-medium text-primary capitalize">{source}</p>
                <p className="text-2xl font-bold text-primary">{stats.messages}</p>
                <p className="text-xs text-muted">
                  Avg score: {(stats.avg_score * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {total === 0 && (
        <div className="card p-8 text-center">
          <p className="text-secondary">No compliance data for the selected period.</p>
          <p className="text-muted text-sm mt-1">
            Compliance scoring runs automatically on agent responses.
          </p>
        </div>
      )}
    </div>
  );
}
