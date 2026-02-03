'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { apiGet } from '@/lib/api';
import ConfirmModal from '@/components/ConfirmModal';
import { logger } from '@/lib/logger';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  client_id: string;
  created_at: string;
}

type TabType = 'overview' | 'history';

export default function UserDetailPage() {
  const params = useParams();
  const userId = params.userId as string;

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab state
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Export state
  const [exportingHistory, setExportingHistory] = useState(false);

  // Confirm modal
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
  }>({
    open: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });

  useEffect(() => {
    if (userId) {
      fetchUserData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fetchUserData is stable
  }, [userId]);

  const fetchUserData = async () => {
    try {
      setLoading(true);

      // Fetch all users and find the one we need
      const usersData = await apiGet<{ users: User[] }>('/api/users');
      const foundUser = usersData.users?.find((u: User) => u.id === userId);

      if (!foundUser) throw new Error('User not found');
      setUser(foundUser);

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleExportChatHistory = async () => {
    if (!user) return;

    try {
      setExportingHistory(true);

      const data = await apiGet<{ export_metadata: { total_conversations: number; total_messages: number }; [key: string]: unknown }>(`/api/users/${userId}/chat-history/export`);

      // Create filename with user name and date
      const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
      const filename = `chat-history-${user.name.replace(/\s+/g, '-')}-${date}.json`;

      // Create blob and download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`Exported ${data.export_metadata.total_conversations} conversations with ${data.export_metadata.total_messages} messages`);
    } catch (error) {
      logger.error('Export error:', error);
      toast.error('Failed to export chat history');
    } finally {
      setExportingHistory(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-muted">Loading user details...</p>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="bg-red-50/20 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error || 'User not found'}</p>
        <Link href="/admin/users" className="mt-2 text-sm text-red-600 hover:text-red-800 underline">
          Back to Users
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="heading-1">{user.name}</h1>
            <span className={user.role === 'admin' ? 'badge-primary' : 'badge-secondary'}>
              {user.role}
            </span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-default mb-6">
        <nav className="flex gap-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'overview'
                ? 'border-primary text-primary font-medium'
                : 'border-transparent text-muted hover:text-primary'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'history'
                ? 'border-primary text-primary font-medium'
                : 'border-transparent text-muted hover:text-primary'
            }`}
          >
            Chat History
          </button>
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="heading-3 mb-4">User Information</h2>
            <div className="space-y-3">
              <div>
                <span className="text-sm text-muted">Email:</span>
                <p className="text-primary">{user.email}</p>
              </div>
              <div>
                <span className="text-sm text-muted">Role:</span>
                <p className="text-primary capitalize">{user.role}</p>
              </div>
              <div>
                <span className="text-sm text-muted">User ID:</span>
                <p className="text-primary font-mono text-sm">{user.id}</p>
              </div>
              <div>
                <span className="text-sm text-muted">Client ID:</span>
                <p className="text-primary font-mono text-sm">{user.client_id}</p>
              </div>
              {user.created_at && (
                <div>
                  <span className="text-sm text-muted">Created:</span>
                  <p className="text-primary">{new Date(user.created_at).toLocaleString()}</p>
                </div>
              )}
            </div>
          </div>

        </div>
      )}

      {/* Chat History Tab */}
      {activeTab === 'history' && (
        <div className="card p-6">
          <h2 className="heading-3 mb-2">Chat History Export</h2>
          <p className="text-sm text-muted mb-4">
            Download all chat messages for this user in JSON format
          </p>
          <button
            onClick={handleExportChatHistory}
            disabled={exportingHistory}
            className="btn-primary "
          >
            {exportingHistory ? 'Exporting...' : 'Export Chat History (JSON)'}
          </button>
        </div>
      )}

      {/* Confirm Modal */}
      <ConfirmModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal({ ...confirmModal, open: false })}
      />
    </div>
  );
}
