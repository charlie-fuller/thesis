'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import LoadingSpinner from './LoadingSpinner';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';

interface TrendData {
  date: string;
  conversations: number;
  documents: number;
  messages: number;
  [key: string]: string | number;  // Dynamic agent keys
}

interface TrendsResponse {
  trends?: TrendData[];
  agents?: string[];  // List of agent names sorted by usage
  agent_totals?: Record<string, number>;
}

// Distinct colors for agents
const AGENT_COLORS: Record<string, string> = {
  'Atlas': '#8b5cf6',      // purple
  'Coordinator': '#3b82f6', // blue
  'Guardian': '#10b981',   // green
  'Fortuna': '#f59e0b',    // amber
  'Oracle': '#ef4444',     // red
  'Sage': '#ec4899',       // pink
  'Architect': '#06b6d4',  // cyan
  'Strategist': '#84cc16', // lime
  'Pioneer': '#f97316',    // orange
  'Operator': '#6366f1',   // indigo
  'Catalyst': '#14b8a6',   // teal
  'Scholar': '#a855f7',    // fuchsia
  'Counselor': '#eab308',  // yellow
  'Echo': '#0ea5e9',       // sky
  'Nexus': '#22c55e',      // emerald
};

// Fallback colors for unknown agents
const FALLBACK_COLORS = [
  '#f472b6', '#60a5fa', '#34d399', '#fbbf24', '#f87171',
  '#c084fc', '#2dd4bf', '#a3e635', '#fb923c', '#818cf8',
];

function getAgentColor(agentName: string, index: number): string {
  return AGENT_COLORS[agentName] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

export default function UsageAnalytics() {
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [agents, setAgents] = useState<string[]>([]);
  const [agentTotals, setAgentTotals] = useState<Record<string, number>>({});
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'agents' | 'activity'>('agents');

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      // Fetch usage trends
      const trendsData = await apiGet<TrendsResponse>(`/api/admin/analytics/usage-trends?days=${days}`);
      logger.debug('📊 Usage Trends Response:', trendsData);
      setTrends(trendsData?.trends || []);
      setAgents(trendsData?.agents || []);
      setAgentTotals(trendsData?.agent_totals || {});
    } catch (error) {
      logger.error('❌ Error fetching analytics:', error);
      // Set empty data on error to prevent crashes
      setTrends([]);
      setAgents([]);
      setAgentTotals({});
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Show helpful message if no data available
  const hasTrends = trends.length > 0 && trends.some(t => t.conversations > 0 || t.documents > 0 || t.messages > 0);
  const hasAgentData = agents.length > 0;
  const hasData = hasTrends || hasAgentData;

  logger.debug('📈 Data Check:', { hasTrends, hasAgentData, hasData, trendsLength: trends.length });

  if (!hasData) {
    return (
      <div className="card p-8 text-center">
        <div className="text-muted mb-4">
          <svg className="w-16 h-16 mx-auto mb-4 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="text-lg font-semibold text-primary mb-2">No Analytics Data Available</h3>
          <p className="text-sm text-secondary mb-4">
            Analytics data will appear here once you start having conversations with agents.
          </p>
          <p className="text-xs text-muted">
            If you have existing data and still see this message, the backend may still be deploying.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-secondary">Time Range:</span>
        <button
          onClick={() => setDays(7)}
          className={`px-3 py-1 text-sm rounded ${days === 7 ? 'bg-primary text-white' : 'bg-surface text-primary hover:bg-surface-hover'}`}
        >
          7 Days
        </button>
        <button
          onClick={() => setDays(30)}
          className={`px-3 py-1 text-sm rounded ${days === 30 ? 'bg-primary text-white' : 'bg-surface text-primary hover:bg-surface-hover'}`}
        >
          30 Days
        </button>
        <button
          onClick={() => setDays(90)}
          className={`px-3 py-1 text-sm rounded ${days === 90 ? 'bg-primary text-white' : 'bg-surface text-primary hover:bg-surface-hover'}`}
        >
          90 Days
        </button>
      </div>

      {/* Tab Selector */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab('agents')}
          className={`px-4 py-2 text-sm font-medium border-b-2 ${
            activeTab === 'agents'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Agent Usage
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`px-4 py-2 text-sm font-medium border-b-2 ${
            activeTab === 'activity'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Activity Breakdown
        </button>
      </div>

      {/* Charts */}
      <div className="card p-6">
        {activeTab === 'agents' ? (
          <div>
            <h3 className="text-lg font-semibold text-primary mb-4">Agent Usage Over Time</h3>
            {agents.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDate}
                    stroke="#888"
                  />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                    labelFormatter={formatDate}
                  />
                  <Legend />
                  {agents.map((agentName, idx) => (
                    <Line
                      key={agentName}
                      type="monotone"
                      dataKey={agentName}
                      stroke={getAgentColor(agentName, idx)}
                      strokeWidth={2}
                      name={agentName}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-secondary">
                No agent usage data available for this period.
              </div>
            )}
          </div>
        ) : (
          <div>
            <h3 className="text-lg font-semibold text-primary mb-4">Activity Breakdown</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  stroke="#888"
                />
                <YAxis stroke="#888" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  labelStyle={{ color: '#fff' }}
                  labelFormatter={formatDate}
                />
                <Legend />
                <Bar dataKey="messages" fill="#8b5cf6" name="Messages" />
                <Bar dataKey="conversations" fill="#3b82f6" name="Conversations" />
                <Bar dataKey="documents" fill="#10b981" name="Documents" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Agent Usage Summary */}
      {agents.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-secondary mb-3">Agent Usage ({days} Days)</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {agents.slice(0, 10).map((agentName, idx) => (
              <div key={agentName} className="card p-3">
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getAgentColor(agentName, idx) }}
                  />
                  <span className="text-sm font-medium text-primary truncate">{agentName}</span>
                </div>
                <div className="text-xl font-bold text-secondary">
                  {agentTotals[agentName]?.toLocaleString() || 0}
                </div>
                <div className="text-xs text-muted">messages</div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
