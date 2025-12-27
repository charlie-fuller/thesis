'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import LazyUsageAnalytics from '@/components/LazyUsageAnalytics';
import QuickActionsPanel from '@/components/QuickActionsPanel';
import InterfaceHealthPanel from '@/components/InterfaceHealthPanel';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';

interface Stats {
  totalConversations: number;
  totalDocuments: number;
  totalUsers: number;
  totalMessages: number;
}

interface StakeholderMetrics {
  total_stakeholders: number;
  engagement_distribution: Record<string, number>;
  average_sentiment: number;
  average_alignment: number;
}

interface Agent {
  id: string;
  name: string;
  display_name: string;
  is_active: boolean;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats>({
    totalConversations: 0,
    totalDocuments: 0,
    totalUsers: 0,
    totalMessages: 0
  });
  const [stakeholderMetrics, setStakeholderMetrics] = useState<StakeholderMetrics | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics'>('overview');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsData, stakeholderData, agentsData] = await Promise.all([
        apiGet<{ total_conversations: number; total_documents: number; total_users: number; total_messages: number }>('/api/admin/stats').catch(() => null),
        apiGet<StakeholderMetrics>('/api/stakeholders/dashboard').catch(() => null),
        apiGet<{ agents: Agent[] }>('/api/agents/').catch(() => ({ agents: [] }))
      ]);

      if (statsData) {
        setStats({
          totalConversations: statsData.total_conversations || 0,
          totalDocuments: statsData.total_documents || 0,
          totalUsers: statsData.total_users || 0,
          totalMessages: statsData.total_messages || 0
        });
      }

      setStakeholderMetrics(stakeholderData);
      setAgents(agentsData?.agents || []);
    } catch (error) {
      logger.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  function getSentimentColor(score: number) {
    if (score > 0.3) return 'text-green-400';
    if (score < -0.3) return 'text-red-400';
    return 'text-gray-400';
  }

  function getEngagementBadge(level: string) {
    switch (level) {
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
  }

  const ENGAGEMENT_LEVELS = ['champion', 'supporter', 'neutral', 'skeptic', 'blocker'];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary">
          Admin Dashboard
        </h1>
        <p className="text-secondary mt-1">
          Thesis platform overview and analytics
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-border mb-8">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'overview'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'analytics'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Usage Analytics
        </button>
      </div>

      {activeTab === 'overview' ? (
        <div className="space-y-8">
          {/* Platform Stats */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-primary mb-6">Platform Stats</h2>
            {loading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="md" />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
                <div className="text-center">
                  <div className="text-4xl font-bold text-teal-400 mb-2">{stats.totalConversations}</div>
                  <div className="text-base font-medium text-secondary">Conversations</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-teal-400 mb-2">{stats.totalDocuments}</div>
                  <div className="text-base font-medium text-secondary">Documents</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-teal-400 mb-2">{stats.totalMessages}</div>
                  <div className="text-base font-medium text-secondary">Messages</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-teal-400 mb-2">{stakeholderMetrics?.total_stakeholders || 0}</div>
                  <div className="text-base font-medium text-secondary">Stakeholders</div>
                </div>
              </div>
            )}
          </div>

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Stakeholder Metrics */}
            {stakeholderMetrics && (
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-primary">Stakeholder Metrics</h2>
                  <Link href="/stakeholders" className="text-sm text-teal-500 hover:underline">
                    View all
                  </Link>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-hover rounded-lg p-4 text-center">
                    <div className={`text-2xl font-bold ${getSentimentColor(stakeholderMetrics.average_sentiment)}`}>
                      {stakeholderMetrics.average_sentiment > 0 ? '+' : ''}{stakeholderMetrics.average_sentiment.toFixed(2)}
                    </div>
                    <div className="text-sm text-secondary">Avg Sentiment</div>
                  </div>
                  <div className="bg-hover rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-teal-400">
                      {Math.round(stakeholderMetrics.average_alignment * 100)}%
                    </div>
                    <div className="text-sm text-secondary">Avg Alignment</div>
                  </div>
                </div>

                {/* Engagement Distribution */}
                <h3 className="text-sm font-medium text-secondary mb-3">Engagement Distribution</h3>
                <div className="space-y-2">
                  {ENGAGEMENT_LEVELS.map(level => {
                    const count = stakeholderMetrics.engagement_distribution[level] || 0;
                    const percentage = stakeholderMetrics.total_stakeholders > 0
                      ? Math.round((count / stakeholderMetrics.total_stakeholders) * 100)
                      : 0;
                    return (
                      <div key={level} className="flex items-center gap-2">
                        <span className={`w-20 px-2 py-0.5 rounded text-xs text-center capitalize ${getEngagementBadge(level)}`}>
                          {level}
                        </span>
                        <div className="flex-1 h-2 bg-hover rounded-full overflow-hidden">
                          <div
                            className={`h-full ${level === 'champion' || level === 'supporter' ? 'bg-teal-500' : level === 'neutral' ? 'bg-gray-400' : 'bg-orange-500'}`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <span className="text-xs text-secondary w-12 text-right">
                          {count}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Agents Status */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-primary">Agents</h2>
                <Link href="/admin/agents" className="text-sm text-teal-500 hover:underline">
                  Manage
                </Link>
              </div>
              {agents.length === 0 ? (
                <p className="text-secondary text-sm">No agents configured</p>
              ) : (
                <div className="space-y-3">
                  {agents.map(agent => (
                    <Link
                      key={agent.id}
                      href={`/admin/agents/${agent.id}`}
                      className="flex items-center justify-between p-3 bg-hover rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${agent.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                        <div>
                          <div className="font-medium text-primary">{agent.display_name}</div>
                          <div className="text-xs text-secondary">{agent.name}</div>
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${agent.is_active ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}>
                        {agent.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <QuickActionsPanel />

          {/* System Health */}
          <InterfaceHealthPanel />
        </div>
      ) : (
        <div>
          <LazyUsageAnalytics />
        </div>
      )}
    </div>
  );
}
