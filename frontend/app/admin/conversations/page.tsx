'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';

interface Conversation {
  id: string;
  title: string;
  client_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  users: {
    name: string;
    email: string;
  };
  clients: {
    name: string;
  };
}

interface Client {
  id: string;
  name: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [clientFilter] = useState('');

  // Bulk export state
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportStartDate, setExportStartDate] = useState('');
  const [exportEndDate, setExportEndDate] = useState('');
  const [exportFormat, setExportFormat] = useState<'json' | 'txt'>('json');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchClients();
    fetchConversations();
  }, [clientFilter]);

  async function fetchClients() {
    try {
      const data = await apiGet<{ clients: Client[] }>('/api/admin/clients');
      setClients(data.clients || []);
    } catch (err) {
      // Silently fail - client dropdown is optional enhancement
      logger.error('Failed to load clients:', err);
    }
  }

  async function fetchConversations() {
    try {
      setLoading(true);
      setError(null);

      let endpoint = `/api/admin/conversations?limit=100`;
      if (clientFilter) {
        endpoint += `&client_id=${clientFilter}`;
      }

      const data = await apiGet<{ conversations: Conversation[] }>(endpoint);
      setConversations(data.conversations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }

  async function handleBulkExport() {
    setExporting(true);
    try {
      let url = `/api/admin/conversations/export?format=${exportFormat}`;
      if (exportStartDate) {
        url += `&start_date=${exportStartDate}`;
      }
      if (exportEndDate) {
        url += `&end_date=${exportEndDate}`;
      }

      // Get auth token
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}${url}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to export conversations');
      }

      // Get filename from Content-Disposition header or generate one
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `conversations-export.${exportFormat}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(downloadUrl);

      toast.success('Conversations exported successfully');
      setShowExportModal(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to export conversations');
    } finally {
      setExporting(false);
    }
  }

  async function handleExport(conversationId: string, format: 'json' | 'txt') {
    try {
      // Fetch conversation messages
      const data = await apiGet<{ messages: Message[] }>(`/api/conversations/${conversationId}/messages`);
      const conversation = conversations.find(c => c.id === conversationId);

      if (format === 'json') {
        // Export as JSON
        const jsonData = JSON.stringify({
          conversation_id: conversationId,
          title: conversation?.title,
          client: conversation?.clients?.name || 'Unknown',
          user: conversation?.users?.name || 'Unknown',
          messages: data.messages
        }, null, 2);

        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${conversationId}.json`;
        a.click();
      } else {
        // Export as TXT
        let txtData = `Conversation: ${conversation?.title}\n`;
        txtData += `Client: ${conversation?.clients?.name || 'Unknown'}\n`;
        txtData += `User: ${conversation?.users?.name || 'Unknown'}\n`;
        txtData += `Date: ${new Date(conversation?.created_at || '').toLocaleDateString()}\n`;
        txtData += `\n${'='.repeat(50)}\n\n`;

        data.messages.forEach((msg: Message) => {
          txtData += `[${msg.role.toUpperCase()}] ${new Date(msg.timestamp).toLocaleString()}\n`;
          txtData += `${msg.content}\n\n`;
        });

        const blob = new Blob([txtData], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${conversationId}.txt`;
        a.click();
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to export conversation');
    }
  }

  // Filter conversations by search query
  const filteredConversations = conversations.filter(conv => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      conv.title.toLowerCase().includes(query) ||
      conv.users?.name?.toLowerCase().includes(query) ||
      conv.users?.email?.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="heading-1">All Conversations</h1>
          <p className="text-muted mt-1">
            View and manage all conversations
          </p>
        </div>
        <button
          onClick={() => setShowExportModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export All
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6">
        {/* Search */}
        <div>
          <label className="label">
            Search
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title or user..."
            className="input-field"
          />
        </div>

        {searchQuery && (
          <div className="mt-3 text-sm text-muted">
            Showing {filteredConversations.length} of {conversations.length} conversations
          </div>
        )}
      </div>

      {/* Conversations List */}
      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      ) : filteredConversations.length === 0 ? (
        <div className="card p-12 text-center">
          <p className="text-muted mb-4">
            {searchQuery ? 'No conversations match your search' : 'No conversations yet'}
          </p>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="link text-sm font-medium"
            >
              Clear search
            </button>
          )}
        </div>
      ) : (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-page border-b border-default">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Conversation
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Messages
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-default">
                {filteredConversations.map((conv) => (
                  <tr key={conv.id} className="hover:bg-hover transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-primary">
                          {conv.title}
                        </div>
                        <div className="text-xs text-muted mt-1">
                          {conv.id.slice(0, 8)}...
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm text-primary">
                          {conv.users?.name || 'Unknown User'}
                        </div>
                        <div className="text-xs text-muted">
                          {conv.users?.email || 'N/A'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-primary">
                        {conv.message_count || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-muted">
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-muted">
                        {new Date(conv.updated_at).toLocaleTimeString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/admin/conversations/${conv.id}`}
                          className="p-1 text-muted hover:text-primary transition-colors cursor-pointer"
                          title="View"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </Link>
                        <button
                          onClick={() => handleExport(conv.id, 'json')}
                          className="p-1 text-muted hover:text-primary transition-colors cursor-pointer"
                          title="Download"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      {!error && conversations.length > 0 && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card p-4">
            <div className="text-sm text-muted mb-1">Total Conversations</div>
            <div className="text-2xl font-bold text-primary">{conversations.length}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-muted mb-1">Total Messages</div>
            <div className="text-2xl font-bold text-primary">
              {conversations.reduce((sum, conv) => sum + (conv.message_count || 0), 0)}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-muted mb-1">Active Users</div>
            <div className="text-2xl font-bold text-primary">
              {new Set(conversations.map(c => c.user_id)).size}
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-semibold text-primary mb-4">Export Conversations</h2>
            <p className="text-sm text-muted mb-6">
              Download all conversation history. Optionally filter by date range.
            </p>

            <div className="space-y-4">
              {/* Date Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Start Date</label>
                  <input
                    type="date"
                    value={exportStartDate}
                    onChange={(e) => setExportStartDate(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="label">End Date</label>
                  <input
                    type="date"
                    value={exportEndDate}
                    onChange={(e) => setExportEndDate(e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>

              {/* Format Selection */}
              <div>
                <label className="label">Export Format</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="exportFormat"
                      value="json"
                      checked={exportFormat === 'json'}
                      onChange={() => setExportFormat('json')}
                      className="text-primary"
                    />
                    <span className="text-sm text-primary">JSON</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="exportFormat"
                      value="txt"
                      checked={exportFormat === 'txt'}
                      onChange={() => setExportFormat('txt')}
                      className="text-primary"
                    />
                    <span className="text-sm text-primary">Text</span>
                  </label>
                </div>
              </div>

              {/* Helper Text */}
              <p className="text-xs text-muted">
                {exportFormat === 'json'
                  ? 'JSON format includes all metadata and is suitable for data analysis or import.'
                  : 'Text format is human-readable and suitable for review or archival.'}
              </p>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowExportModal(false);
                  setExportStartDate('');
                  setExportEndDate('');
                }}
                className="btn-secondary"
                disabled={exporting}
              >
                Cancel
              </button>
              <button
                onClick={handleBulkExport}
                disabled={exporting}
                className="btn-primary flex items-center gap-2"
              >
                {exporting ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Export
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
