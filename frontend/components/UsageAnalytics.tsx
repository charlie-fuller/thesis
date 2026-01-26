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

interface DiscoTrendData {
  date: string;
  [key: string]: string | number;  // Dynamic agent keys
}

interface DiscoTrendsResponse {
  trends?: DiscoTrendData[];
  agents?: string[];
  agent_totals?: Record<string, number>;
  total_runs?: number;
}

// Distinct colors for agents
const AGENT_COLORS: Record<string, string> = {
  'Atlas': '#8b5cf6',      // purple
  'Coordinator': '#3b82f6', // blue
  'Guardian': '#10b981',   // green
  'Capital': '#f59e0b',    // amber
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

// DISCo agent colors (matching DISCo workflow stages)
const DISCO_AGENT_COLORS: Record<string, string> = {
  'triage': '#3b82f6',           // blue - Discovery
  'discovery_planner': '#f59e0b', // amber - Discovery
  'coverage_tracker': '#8b5cf6',  // purple - Discovery
  'insight_extractor': '#06b6d4', // cyan - Intelligence
  'consolidator': '#14b8a6',      // teal - Intelligence
  'synthesizer': '#22c55e',       // green - Synthesis
  'strategist': '#10b981',        // emerald - Synthesis
  'prd_generator': '#f43f5e',     // rose - Capabilities
  'tech_evaluation': '#6366f1',   // indigo - Capabilities
};

// Display names for DISCo agents
const DISCO_AGENT_NAMES: Record<string, string> = {
  'triage': 'Triage',
  'discovery_planner': 'Discovery Planner',
  'coverage_tracker': 'Coverage Tracker',
  'insight_extractor': 'Insight Extractor',
  'consolidator': 'Consolidator',
  'synthesizer': 'Synthesizer',
  'strategist': 'Strategist',
  'prd_generator': 'PRD Generator',
  'tech_evaluation': 'Tech Evaluation',
};

function getAgentColor(agentName: string, index: number): string {
  return AGENT_COLORS[agentName] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

function getDiscoAgentColor(agentName: string, index: number): string {
  return DISCO_AGENT_COLORS[agentName] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

function getDiscoAgentDisplayName(agentName: string): string {
  return DISCO_AGENT_NAMES[agentName] || agentName;
}

export default function UsageAnalytics() {
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [agents, setAgents] = useState<string[]>([]);
  const [agentTotals, setAgentTotals] = useState<Record<string, number>>({});
  const [discoTrends, setDiscoTrends] = useState<DiscoTrendData[]>([]);
  const [discoAgents, setDiscoAgents] = useState<string[]>([]);
  const [discoAgentTotals, setDiscoAgentTotals] = useState<Record<string, number>>({});
  const [discoTotalRuns, setDiscoTotalRuns] = useState(0);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'agents' | 'activity' | 'disco'>('agents');

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      // Fetch usage trends and DISCo trends in parallel
      const [trendsData, discoData] = await Promise.all([
        apiGet<TrendsResponse>(`/api/admin/analytics/usage-trends?days=${days}`),
        apiGet<DiscoTrendsResponse>(`/api/disco/analytics/usage?days=${days}`).catch(() => null),
      ]);

      logger.debug('Usage Trends Response:', trendsData);
      setTrends(trendsData?.trends || []);
      setAgents(trendsData?.agents || []);
      setAgentTotals(trendsData?.agent_totals || {});

      if (discoData) {
        logger.debug('DISCo Trends Response:', discoData);
        setDiscoTrends(discoData.trends || []);
        setDiscoAgents(discoData.agents || []);
        setDiscoAgentTotals(discoData.agent_totals || {});
        setDiscoTotalRuns(discoData.total_runs || 0);
      }
    } catch (error) {
      logger.error('Error fetching analytics:', error);
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

  logger.debug('Data Check:', { hasTrends, hasAgentData, hasData, trendsLength: trends.length });

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
        <button
          onClick={() => setActiveTab('disco')}
          className={`px-4 py-2 text-sm font-medium border-b-2 ${
            activeTab === 'disco'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          DISCo Usage
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
        ) : activeTab === 'activity' ? (
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
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-primary">DISCo Agent Usage</h3>
              <span className="text-sm text-secondary">
                Total Runs: <span className="font-semibold text-primary">{discoTotalRuns}</span>
              </span>
            </div>

            {/* Agent summary cards */}
            {discoAgents.length > 0 && (
              <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-9 gap-2 mb-6">
                {discoAgents.map((agent, idx) => (
                  <div
                    key={agent}
                    className="p-2 rounded-lg text-center"
                    style={{ backgroundColor: `${getDiscoAgentColor(agent, idx)}20` }}
                  >
                    <div
                      className="text-lg font-bold"
                      style={{ color: getDiscoAgentColor(agent, idx) }}
                    >
                      {discoAgentTotals[agent] || 0}
                    </div>
                    <div className="text-xs text-secondary truncate" title={getDiscoAgentDisplayName(agent)}>
                      {getDiscoAgentDisplayName(agent).split(' ')[0]}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Chart */}
            {discoAgents.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={discoTrends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDate}
                    stroke="#888"
                  />
                  <YAxis stroke="#888" allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                    labelFormatter={formatDate}
                    formatter={(value, name) => [value ?? 0, getDiscoAgentDisplayName(String(name))]}
                  />
                  <Legend formatter={(value) => getDiscoAgentDisplayName(value)} />
                  {discoAgents.map((agentName, idx) => (
                    <Line
                      key={agentName}
                      type="monotone"
                      dataKey={agentName}
                      stroke={getDiscoAgentColor(agentName, idx)}
                      strokeWidth={2}
                      name={agentName}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-secondary">
                <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p>No DISCo usage data available for this period.</p>
                <p className="text-sm mt-1">Run some DISCo agents to see analytics here.</p>
              </div>
            )}
          </div>
        )}
      </div>

    </div>
  );
}
