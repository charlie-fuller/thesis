'use client';

import { useState, useEffect } from 'react';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from './LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';

interface UploadHealth {
  periods: {
    '24h': {
      total: number;
      completed: number;
      failed: number;
      pending: number;
      processing: number;
      success_rate: number;
      failed_by_type: Record<string, number>;
    };
    '7d': {
      total: number;
      completed: number;
      failed: number;
      success_rate: number;
      failed_by_type: Record<string, number>;
    };
    '30d': {
      total: number;
      completed: number;
      failed: number;
      success_rate: number;
    };
  };
  stuck_documents: Array<{
    id: string;
    filename: string;
    status: string;
    uploaded_at: string;
  }>;
  recent_failures: Array<{
    id: string;
    filename: string;
    error: string;
    uploaded_at: string;
  }>;
}

interface InterfaceHealth {
  response_metrics: {
    avg_word_count: number;
    total_responses: number;
    target: number;
    status: 'healthy' | 'warning' | 'critical';
  };
  image_metrics: {
    suggestions: number;
    generated: number;
    completion_rate: number;
  };
  workflow_metrics: {
    avg_turns_to_useable: number;
    conversations_tracked: number;
    stuck_conversations: number;
    stuck_status: 'healthy' | 'warning' | 'critical';
  };
  period: string;
}

export default function InterfaceHealthPanel() {
  const { user, loading: authLoading } = useAuth();
  const [uploadHealth, setUploadHealth] = useState<UploadHealth | null>(null);
  const [interfaceHealth, setInterfaceHealth] = useState<InterfaceHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Wait for auth to complete before fetching data
    if (authLoading || !user) {
      return;
    }

    fetchHealthData();
    // Refresh every 2 minutes
    const interval = setInterval(fetchHealthData, 120000);
    return () => clearInterval(interval);
  }, [authLoading, user]);

  const fetchHealthData = async () => {
    try {
      setError(null);
      const [uploadData, interfaceData] = await Promise.all([
        apiGet<{ success: boolean } & UploadHealth>('/api/admin/analytics/upload-health'),
        apiGet<{ success: boolean } & InterfaceHealth>('/api/admin/analytics/interface-health')
      ]);

      if (uploadData.success) {
        setUploadHealth(uploadData);
      }
      if (interfaceData.success) {
        setInterfaceHealth(interfaceData);
      }
    } catch (err) {
      logger.error('Error fetching health data:', err);
      setError('Failed to load health metrics');
    } finally {
      setLoading(false);
    }
  };

  // getStatusColor kept for potential future use in expanded health details
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _getStatusColor = (status: 'healthy' | 'warning' | 'critical' | string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'critical':
        return 'text-red-400';
      default:
        return 'text-secondary';
    }
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 95) return 'text-green-400';
    if (rate >= 85) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSuccessRateStatus = (rate: number): 'healthy' | 'warning' | 'critical' => {
    if (rate >= 95) return 'healthy';
    if (rate >= 85) return 'warning';
    return 'critical';
  };

  const getWordCountColor = (count: number) => {
    if (count <= 500) return 'text-green-400';
    if (count <= 800) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getStuckColor = (count: number) => {
    if (count === 0) return 'text-green-400';
    if (count <= 2) return 'text-yellow-400';
    return 'text-red-400';
  };

  // Determine overall health status
  const getOverallStatus = (): 'healthy' | 'warning' | 'critical' => {
    if (!uploadHealth || !interfaceHealth) return 'healthy';

    const uploadStatus = getSuccessRateStatus(uploadHealth.periods['24h'].success_rate);
    const responseStatus = interfaceHealth.response_metrics.status;
    const stuckStatus = interfaceHealth.workflow_metrics.stuck_status;

    if (uploadStatus === 'critical' || responseStatus === 'critical' || stuckStatus === 'critical') {
      return 'critical';
    }
    if (uploadStatus === 'warning' || responseStatus === 'warning' || stuckStatus === 'warning') {
      return 'warning';
    }
    return 'healthy';
  };

  const getOverallStatusText = () => {
    const status = getOverallStatus();
    switch (status) {
      case 'healthy':
        return 'All Healthy';
      case 'warning':
        return 'Some Warnings';
      case 'critical':
        return 'Needs Attention';
      default:
        return 'Unknown';
    }
  };

  const getOverallStatusColor = () => {
    const status = getOverallStatus();
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'critical':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-6">Interface Health</h3>
        <div className="flex justify-center py-12">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-6">Interface Health</h3>
        <div className="text-center py-8 text-secondary">{error}</div>
      </div>
    );
  }

  const upload24h = uploadHealth?.periods['24h'];
  const response = interfaceHealth?.response_metrics;
  const images = interfaceHealth?.image_metrics;
  const workflow = interfaceHealth?.workflow_metrics;

  return (
    <div className="card p-6">
      {/* Header with Overall Status */}
      <div className="flex items-center gap-3 mb-8">
        <div className={`w-3 h-3 rounded-full ${getOverallStatusColor()} animate-pulse`}></div>
        <div>
          <h3 className="text-lg font-semibold text-primary">Interface Health</h3>
          <p className="text-sm text-secondary">{getOverallStatusText()} (Last 7 days)</p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-8 md:gap-12">
        {/* Upload Health */}
        <div className="text-center group relative">
          <div className={`text-3xl font-bold mb-2 ${getSuccessRateColor(upload24h?.success_rate ?? 100)}`}>
            {upload24h?.success_rate ?? 100}%
          </div>
          <div className="text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Uploads
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-sm text-muted">
            {upload24h?.failed ?? 0} failed (24h)
          </div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-48 z-10 pointer-events-none">
            <div className="font-medium mb-1">Document Upload Success Rate</div>
            <div className="text-gray-300">Percentage of user file uploads that completed processing successfully in the last 24 hours.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>

        {/* Image Generation */}
        <div className="text-center group relative">
          <div className="text-3xl font-bold mb-2 text-blue-400">
            {images?.generated ?? 0}
          </div>
          <div className="text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Images
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-sm text-muted">
            {images?.suggestions ?? 0} suggested
          </div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-56 z-10 pointer-events-none">
            <div className="font-medium mb-1">AI Image Generation (7 days)</div>
            <div className="text-gray-300">Number of images actually generated by users. &quot;Suggested&quot; shows how many times Thesis offered to create an image.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>

        {/* Response Length */}
        <div className="text-center group relative">
          <div className={`text-3xl font-bold mb-2 ${getWordCountColor(response?.avg_word_count ?? 0)}`}>
            {response?.avg_word_count ?? 0}
          </div>
          <div className="text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Avg Words
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-sm text-muted">
            Target: {response?.target ?? 500}
          </div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-52 z-10 pointer-events-none">
            <div className="font-medium mb-1">Average Response Length</div>
            <div className="text-gray-300">Average word count of Thesis&apos;s responses over the last 7 days. Target is ≤500 words for concise, focused answers.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>

        {/* Workflow Health */}
        <div className="text-center group relative">
          <div className={`text-3xl font-bold mb-2 ${getStuckColor(workflow?.stuck_conversations ?? 0)}`}>
            {workflow?.stuck_conversations ?? 0}
          </div>
          <div className="text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Stuck
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-sm text-muted">
            {workflow?.avg_turns_to_useable ?? 0} avg turns
          </div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-56 z-10 pointer-events-none">
            <div className="font-medium mb-1">Stuck Conversations</div>
            <div className="text-gray-300">Conversations waiting for user response to an image suggestion for &gt;5 minutes. &quot;Avg turns&quot; shows typical exchanges before reaching useable output.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>
      </div>

      {/* Expandable Details */}
      {((uploadHealth?.stuck_documents?.length ?? 0) > 0 || (uploadHealth?.recent_failures?.length ?? 0) > 0) && (
        <div className="mt-8 pt-6 border-t border-border">
          <h4 className="text-sm font-medium text-secondary mb-4">Issues Requiring Attention</h4>

          {/* Stuck Documents */}
          {(uploadHealth?.stuck_documents?.length ?? 0) > 0 && (
            <div className="mb-4">
              <div className="text-xs font-medium text-yellow-400 mb-2">
                Stuck Documents ({uploadHealth?.stuck_documents.length})
              </div>
              <div className="space-y-1">
                {uploadHealth?.stuck_documents.slice(0, 3).map((doc) => (
                  <div key={doc.id} className="text-xs text-muted truncate">
                    {doc.filename} - {doc.status}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Failures */}
          {(uploadHealth?.recent_failures?.length ?? 0) > 0 && (
            <div>
              <div className="text-xs font-medium text-red-400 mb-2">
                Recent Failures ({uploadHealth?.recent_failures.length})
              </div>
              <div className="space-y-1">
                {uploadHealth?.recent_failures.slice(0, 3).map((doc) => (
                  <div key={doc.id} className="text-xs text-muted truncate">
                    {doc.filename} - {doc.error}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
