'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';
import { useAuth } from '@/contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';

export default function QuickActionsPanel() {
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded' | 'down'>('healthy');
  const [healthMetrics, setHealthMetrics] = useState({
    supabase: { status: 'checking', responseTime: 0 },
    railway: { status: 'checking', uptime: false },
    anthropic: { status: 'checking', latency: 0 },
    voyageAI: { status: 'checking', latency: 0 },
    neo4j: { status: 'checking', responseTime: 0 }
  });
  const [loading, setLoading] = useState(true);
  const { session, loading: authLoading } = useAuth();

  const fetchHealthMetrics = useCallback(async () => {
    // Don't fetch if not authenticated
    if (!session) {
      setLoading(false);
      return;
    }

    try {
      const response = await apiGet<{ success: boolean; health: {
        supabase: { status: string; responseTime: number };
        railway: { status: string; uptime: boolean };
        anthropic: { status: string; latency: number };
        voyageAI: { status: string; latency: number };
        neo4j: { status: string; responseTime: number };
      } }>('/api/admin/health');
      logger.debug('Health check response:', response);

      if (response.success && response.health) {
        logger.debug('Health data:', response.health);
        setHealthMetrics(response.health);

        // Determine overall system status based on all services
        const { supabase, railway, anthropic, voyageAI, neo4j } = response.health;

        // Critical services: Supabase and Railway must be up
        if (supabase.status === 'error' || railway.status === 'error') {
          setSystemStatus('down');
        }
        // All critical services operational
        // Non-critical services (Anthropic, Voyage AI, Neo4j) can be idle, active, not_configured, or unknown
        else if (
          supabase.status === 'connected' &&
          railway.status === 'running'
        ) {
          // Check if auxiliary services have actual errors
          const errorStatuses = ['error', 'down', 'auth_error'];
          const warningStatuses = ['not_configured', 'rate_limited'];

          const anthropicError = errorStatuses.includes(anthropic.status);
          const voyageError = errorStatuses.includes(voyageAI.status);
          const neo4jError = errorStatuses.includes(neo4j.status);

          const anthropicWarning = warningStatuses.includes(anthropic.status);
          const voyageWarning = warningStatuses.includes(voyageAI.status);
          const neo4jWarning = warningStatuses.includes(neo4j.status);

          if (anthropicError || voyageError || neo4jError) {
            setSystemStatus('degraded');
          } else if (anthropicWarning || voyageWarning || neo4jWarning) {
            // Warnings are still considered healthy overall, but could show degraded if desired
            setSystemStatus('healthy');
          } else {
            setSystemStatus('healthy');
          }
        }
        // Some services degraded but system functional
        else {
          setSystemStatus('degraded');
        }
      } else {
        logger.warn('Health check returned unexpected response:', response);
        setSystemStatus('degraded');
      }
    } catch (error) {
      logger.error('Error fetching health metrics:', error);
      logger.error('Full error details:', error);
      // Don't immediately mark as down - could be temporary network issue
      setSystemStatus('degraded');
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    // Wait for auth to be ready before fetching
    if (authLoading) return;

    if (session) {
      fetchHealthMetrics();
      // Refresh every 60 seconds
      const interval = setInterval(fetchHealthMetrics, 60000);
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [authLoading, session, fetchHealthMetrics]);

  // Service status color coding
  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'running':
      case 'deployed':
      case 'active':
        return 'text-green-400';
      case 'idle':
        return 'text-blue-400';
      case 'error':
      case 'down':
        return 'text-red-400';
      default:
        return 'text-secondary';
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for future metrics display
  const _getResponseTimeColor = (ms: number) => {
    if (ms === 0) return 'text-secondary';
    if (ms <= 100) return 'text-green-400';
    if (ms <= 300) return 'text-yellow-400';
    return 'text-red-400';
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for future metrics display
  const _getLatencyColor = (seconds: number) => {
    if (seconds === 0) return 'text-secondary';
    if (seconds <= 2) return 'text-green-400';
    if (seconds <= 5) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getStatusColor = () => {
    switch (systemStatus) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'down':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (systemStatus) {
      case 'healthy':
        return 'All Operational';
      case 'degraded':
        return 'Degraded Performance';
      case 'down':
        return 'Down';
      default:
        return 'Unknown Status';
    }
  };

  // Format service status with metrics
  const formatSupabaseStatus = () => {
    const status = healthMetrics.supabase?.status || 'checking';
    const responseTime = healthMetrics.supabase?.responseTime || 0;

    if (status === 'error' || status === 'down') {
      return 'Error';
    }

    if (status === 'checking' || responseTime === 0) {
      return 'Checking';
    }

    // Return performance description based on response time
    if (responseTime <= 100) return 'Fast';
    if (responseTime <= 300) return 'Good';
    return 'Slow';
  };

  const formatAnthropicStatus = () => {
    const status = healthMetrics.anthropic?.status || 'checking';
    const latency = healthMetrics.anthropic?.latency || 0;

    // Handle special statuses
    if (status === 'not_configured') return 'Not Set';
    if (status === 'auth_error') return 'Auth Error';
    if (status === 'rate_limited') return 'Rate Limited';
    if (status === 'error') return 'Error';

    if (latency > 0) {
      return `Connected (${latency.toFixed(1)}s)`;
    }
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const formatVoyageStatus = () => {
    const status = healthMetrics.voyageAI?.status || 'checking';
    const latency = healthMetrics.voyageAI?.latency || 0;

    // Handle special statuses
    if (status === 'not_configured') return 'Not Set';
    if (status === 'auth_error') return 'Auth Error';
    if (status === 'rate_limited') return 'Rate Limited';
    if (status === 'error') return 'Error';

    if (latency > 0) {
      return `Connected (${latency.toFixed(1)}s)`;
    }
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  // Determine color based on combined status + metric
  const getSupabaseColor = () => {
    const status = healthMetrics.supabase?.status || 'checking';
    const responseTime = healthMetrics.supabase?.responseTime || 0;

    if (status === 'error' || status === 'down') return 'text-red-400';
    if (status === 'checking') return 'text-secondary';

    // Color based on response time if connected
    if (responseTime === 0) return 'text-green-400';
    if (responseTime <= 100) return 'text-green-400';
    if (responseTime <= 300) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getAnthropicColor = () => {
    const status = healthMetrics.anthropic?.status || 'checking';
    const latency = healthMetrics.anthropic?.latency || 0;

    if (status === 'error' || status === 'down' || status === 'auth_error') return 'text-red-400';
    if (status === 'not_configured') return 'text-yellow-400';
    if (status === 'rate_limited') return 'text-orange-400';
    if (status === 'checking') return 'text-secondary';
    if (status === 'idle') return 'text-blue-400';

    // Color based on latency if connected
    if (latency === 0) return 'text-green-400';
    if (latency <= 2) return 'text-green-400';
    if (latency <= 5) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getVoyageColor = () => {
    const status = healthMetrics.voyageAI?.status || 'checking';
    const latency = healthMetrics.voyageAI?.latency || 0;

    if (status === 'error' || status === 'down' || status === 'auth_error') return 'text-red-400';
    if (status === 'not_configured') return 'text-yellow-400';
    if (status === 'rate_limited') return 'text-orange-400';
    if (status === 'checking') return 'text-secondary';
    if (status === 'idle') return 'text-blue-400';

    // Color based on latency if connected
    if (latency === 0) return 'text-green-400';
    if (latency <= 2) return 'text-green-400';
    if (latency <= 5) return 'text-yellow-400';
    return 'text-red-400';
  };

  const formatNeo4jStatus = () => {
    const status = healthMetrics.neo4j?.status || 'checking';
    const responseTime = healthMetrics.neo4j?.responseTime || 0;

    if (status === 'error' || status === 'down') {
      return 'Error';
    }

    if (status === 'not_configured') {
      return 'Not Set';
    }

    if (status === 'checking' || responseTime === 0) {
      return 'Checking';
    }

    // Return performance description based on response time
    if (responseTime <= 200) return 'Fast';
    if (responseTime <= 500) return 'Good';
    return 'Slow';
  };

  const getNeo4jColor = () => {
    const status = healthMetrics.neo4j?.status || 'checking';
    const responseTime = healthMetrics.neo4j?.responseTime || 0;

    if (status === 'error' || status === 'down') return 'text-red-400';
    if (status === 'not_configured') return 'text-yellow-400';
    if (status === 'checking') return 'text-secondary';

    // Color based on response time if connected
    if (responseTime === 0) return 'text-green-400';
    if (responseTime <= 200) return 'text-green-400';
    if (responseTime <= 500) return 'text-yellow-400';
    return 'text-red-400';
  };

  if (loading) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-6">System Health</h3>
        <div className="flex justify-center py-12">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      {/* Header with Overall Status */}
      <div className="flex items-center gap-3 mb-8">
        <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`}></div>
        <div>
          <h3 className="text-lg font-semibold text-primary">System Health</h3>
          <p className="text-sm text-secondary">{getStatusText()}</p>
        </div>
      </div>

      {/* Service Status Grid */}
      <div className="grid grid-cols-5 gap-4 md:gap-8">
        {/* Supabase (DB) */}
        <div className="text-center group relative">
          <div className={`text-2xl md:text-3xl font-bold mb-2 ${getSupabaseColor()}`}>
            {formatSupabaseStatus()}
          </div>
          <div className="text-sm md:text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Supabase
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-xs md:text-sm text-muted">PostgreSQL</div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-48 z-10 pointer-events-none">
            <div className="font-medium mb-1">Database Connection</div>
            <div className="text-gray-300">PostgreSQL database hosted on Supabase. Stores all user data, conversations, and documents.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>

        {/* Neo4j (Graph DB) */}
        <div className="text-center group relative">
          <div className={`text-2xl md:text-3xl font-bold mb-2 ${getNeo4jColor()}`}>
            {formatNeo4jStatus()}
          </div>
          <div className="text-sm md:text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Neo4j
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-xs md:text-sm text-muted">Graph DB</div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-52 z-10 pointer-events-none">
            <div className="font-medium mb-1">Graph Database</div>
            <div className="text-gray-300">Neo4j Aura graph database. Stores stakeholder relationships, agent connections, and knowledge graphs.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>

        {/* Railway (API) */}
        <div className="text-center group relative">
          <div className={`text-2xl md:text-3xl font-bold mb-2 capitalize ${getServiceStatusColor(healthMetrics.railway?.status || 'checking')}`}>
            {healthMetrics.railway?.status || 'Checking'}
          </div>
          <div className="text-sm md:text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Railway
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-xs md:text-sm text-muted">Backend</div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-48 z-10 pointer-events-none">
            <div className="font-medium mb-1">Backend API Server</div>
            <div className="text-gray-300">FastAPI backend hosted on Railway. Handles all API requests, chat processing, and integrations.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>

        {/* Anthropic (Claude) */}
        <div className="text-center group relative">
          <div className={`text-2xl md:text-3xl font-bold mb-2 ${getAnthropicColor()}`}>
            {formatAnthropicStatus()}
          </div>
          <div className="text-sm md:text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Anthropic
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-xs md:text-sm text-muted">LLM</div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-52 z-10 pointer-events-none">
            <div className="font-medium mb-1">Claude AI (LLM)</div>
            <div className="text-gray-300">Powers all chat responses using Claude. Shows &quot;idle&quot; when no recent requests, &quot;active&quot; with latency when processing.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>

        {/* Voyage AI (Embeddings) */}
        <div className="text-center group relative">
          <div className={`text-2xl md:text-3xl font-bold mb-2 ${getVoyageColor()}`}>
            {formatVoyageStatus()}
          </div>
          <div className="text-sm md:text-base font-medium text-secondary mb-1 flex items-center justify-center gap-1">
            Voyage AI
            <svg className="w-4 h-4 text-muted opacity-50 group-hover:opacity-100 transition-opacity cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-xs md:text-sm text-muted">Embeddings</div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 w-52 z-10 pointer-events-none">
            <div className="font-medium mb-1">Vector Embeddings</div>
            <div className="text-gray-300">Generates embeddings for document search and help system. Shows &quot;idle&quot; when no recent requests.</div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
