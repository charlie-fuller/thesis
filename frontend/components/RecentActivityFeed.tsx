'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import LoadingSpinner from './LoadingSpinner';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';

interface ActivityItem {
  type: 'conversation' | 'document' | 'user_registration';
  id: string;
  timestamp: string;
  user?: {
    id: string;
    name: string;
    email: string;
  };
  // Conversation fields
  title?: string;
  message_count?: number;
  // Document fields
  filename?: string;
  file_size?: number;
  // User registration fields
  name?: string;
  email?: string;
  role?: string;
}

export default function RecentActivityFeed() {
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(20);

  useEffect(() => {
    fetchActivity();
  }, [limit]);

  const fetchActivity = async () => {
    setLoading(true);
    try {
      const data = await apiGet<{ activity: ActivityItem[] }>(`/api/admin/analytics/recent-activity?limit=${limit}`);
      setActivity(data.activity);
    } catch (error) {
      logger.error('Error fetching activity:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'conversation':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        );
      case 'document':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'user_registration':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'conversation':
        return 'bg-blue-500/10 text-blue-400';
      case 'document':
        return 'bg-green-500/10 text-green-400';
      case 'user_registration':
        return 'bg-amber-500/10 text-amber-400';
      default:
        return 'bg-surface text-primary';
    }
  };

  const renderActivityItem = (item: ActivityItem) => {
    switch (item.type) {
      case 'conversation':
        return (
          <Link href={`/admin/conversations/${item.id}`} key={item.id}>
            <div className="flex items-center gap-6 p-3 rounded-lg hover:bg-surface-hover transition-colors cursor-pointer">
              <div className={`p-2 rounded-lg flex-shrink-0 ${getActivityColor(item.type)}`}>
                {getActivityIcon(item.type)}
              </div>
              <div className="w-96 min-w-0">
                <p className="text-sm text-primary font-medium truncate">
                  {item.title || 'Untitled Conversation'}
                </p>
              </div>
              <div className="flex-shrink-0 text-sm text-secondary w-28">
                {item.message_count || 0} messages
              </div>
              <div className="flex-shrink-0 text-sm text-secondary w-40 truncate">
                {item.user?.name || 'Unknown User'}
              </div>
              <div className="flex-shrink-0 text-sm text-secondary whitespace-nowrap w-20">
                {formatTimestamp(item.timestamp)}
              </div>
            </div>
          </Link>
        );

      case 'document':
        return (
          <div key={item.id} className="flex items-center gap-6 p-3 rounded-lg">
            <div className={`p-2 rounded-lg flex-shrink-0 ${getActivityColor(item.type)}`}>
              {getActivityIcon(item.type)}
            </div>
            <div className="w-96 min-w-0">
              <p className="text-sm text-primary font-medium truncate">
                {item.filename}
              </p>
            </div>
            <div className="flex-shrink-0 text-sm text-secondary w-28">
              {formatFileSize(item.file_size || 0)}
            </div>
            <div className="flex-shrink-0 text-sm text-secondary w-40 truncate">
              {item.user?.name || 'Unknown User'}
            </div>
            <div className="flex-shrink-0 text-sm text-secondary whitespace-nowrap w-20">
              {formatTimestamp(item.timestamp)}
            </div>
          </div>
        );

      case 'user_registration':
        return (
          <Link href={`/admin/users/${item.id}`} key={item.id}>
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-hover transition-colors cursor-pointer">
              <div className={`p-2 rounded-lg ${getActivityColor(item.type)}`}>
                {getActivityIcon(item.type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-primary font-medium truncate">
                  {item.name}
                </p>
                <p className="text-xs text-secondary">
                  {item.email} • {item.role}
                </p>
              </div>
              <span className="text-xs text-secondary whitespace-nowrap">
                {formatTimestamp(item.timestamp)}
              </span>
            </div>
          </Link>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (activity.length === 0) {
    return (
      <div className="text-center py-8 text-secondary">
        No recent activity
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="space-y-1">
        {activity.map(renderActivityItem)}
      </div>

      {/* Load More Button */}
      {activity.length >= limit && (
        <div className="pt-4 text-center">
          <button
            onClick={() => setLimit(limit + 20)}
            className="px-4 py-2 text-sm bg-surface hover:bg-surface-hover text-primary rounded-lg transition-colors"
          >
            Load More
          </button>
        </div>
      )}
    </div>
  );
}
