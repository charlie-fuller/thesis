'use client';

import { useState, useEffect } from 'react';
import LazyUsageAnalytics from '@/components/LazyUsageAnalytics';
import QuickActionsPanel from '@/components/QuickActionsPanel';
import InterfaceHealthPanel from '@/components/InterfaceHealthPanel';
import LoadingSpinner from '@/components/LoadingSpinner';
import IdeationVelocityCard from '@/components/IdeationVelocityCard';
import OutputActivityCard from '@/components/OutputActivityCard';
import KeywordTrendsCard from '@/components/KeywordTrendsCard';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';

interface Stats {
  totalConversations: number;
  totalDocuments: number;
  totalUsers: number;
  totalMessages: number;
}

interface User {
  id: string;
  email: string;
  name?: string;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats>({
    totalConversations: 0,
    totalDocuments: 0,
    totalUsers: 0,
    totalMessages: 0
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'kpis' | 'analytics'>('overview');
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | undefined>(undefined); // undefined = "All Users"
  const [loadingUsers, setLoadingUsers] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'kpis') {
      fetchUsers();
    }
  }, [activeTab]);

  const fetchStats = async () => {
    try {
      const data = await apiGet<{ total_conversations: number; total_documents: number; total_users: number; total_messages: number }>('/api/admin/stats');

      setStats({
        totalConversations: data.total_conversations || 0,
        totalDocuments: data.total_documents || 0,
        totalUsers: data.total_users || 0,
        totalMessages: data.total_messages || 0
      });
    } catch (error) {
      logger.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      setLoadingUsers(true);
      const data = await apiGet<{ users: User[] }>('/api/admin/users');
      setUsers(data.users || []);
    } catch (error) {
      logger.error('Error fetching users:', error);
    } finally {
      setLoadingUsers(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary">
          Admin Dashboard
        </h1>
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
          onClick={() => setActiveTab('kpis')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'kpis'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          KPI Dashboard
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
          {/* Quick Stats */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-primary mb-6">Quick Stats</h2>
            {loading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="md" />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 mb-2">{stats.totalUsers}</div>
                  <div className="text-base font-medium text-secondary">Total Users</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 mb-2">{stats.totalConversations}</div>
                  <div className="text-base font-medium text-secondary">Conversations</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 mb-2">{stats.totalDocuments}</div>
                  <div className="text-base font-medium text-secondary">Documents</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 mb-2">{stats.totalMessages}</div>
                  <div className="text-base font-medium text-secondary">Messages</div>
                </div>
              </div>
            )}
          </div>

          {/* System Health Panel */}
          <QuickActionsPanel />

          {/* Interface Health Panel */}
          <InterfaceHealthPanel />
        </div>
      ) : activeTab === 'kpis' ? (
        <div className="space-y-8">
          {/* KPI Dashboard Header */}
          <div className="card p-6">
            <h2 className="text-xl font-bold text-primary mb-2">Bradbury Impact Loop KPIs</h2>
            <p className="text-sm text-secondary">
              Measuring system effectiveness through the Bradbury Impact Loop methodology.
              These KPIs evaluate the Solomon Engine framework&apos;s ability to drive behavior change and knowledge application.
            </p>

            {/* User Selector */}
            <div className="mt-4 flex items-center gap-3">
              <label htmlFor="user-select" className="text-sm font-medium text-primary">
                Show metrics for:
              </label>
              <select
                id="user-select"
                value={selectedUserId || ''}
                onChange={(e) => setSelectedUserId(e.target.value || undefined)}
                className="input-field px-3 py-2 text-sm"
                disabled={loadingUsers}
              >
                <option value="">All Users</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name || user.email}
                  </option>
                ))}
              </select>
              {loadingUsers && <LoadingSpinner size="sm" />}
            </div>
          </div>

          {/* KPI Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <IdeationVelocityCard
              timePeriod="week"
              userId={selectedUserId}
            />
            <OutputActivityCard
              timePeriod="month"
              userId={selectedUserId}
            />
          </div>

          {/* Keyword Trends - Full Width */}
          <KeywordTrendsCard />
        </div>
      ) : (
        <div>
          <LazyUsageAnalytics />
        </div>
      )}
    </div>
  );
}
