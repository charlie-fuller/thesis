'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from './LoadingSpinner';

interface HelpStatus {
  status: string;
  total_documents: number;
  total_chunks: number;
  indexing_status: string;
  categories?: Record<string, number>;
  by_role?: {
    admin: { documents: number; chunks: number };
    user: { documents: number; chunks: number };
  };
}

interface IndexingStatus {
  is_indexing: boolean;
  status: 'idle' | 'running' | 'completed' | 'error';
  progress: number;
  total_files: number;
  current_file: string;
  started_at: string | null;
  completed_at: string | null;
  result: { total_documents: number; total_chunks: number } | null;
  error: string | null;
}

export default function HelpSystemPanel() {
  const [helpStatus, setHelpStatus] = useState<HelpStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [indexingStatus, setIndexingStatus] = useState<IndexingStatus | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchHelpStatus();
    // Check if there's an ongoing indexing operation
    checkIndexingStatus();

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const fetchHelpStatus = async () => {
    try {
      const response = await apiGet<HelpStatus>('/api/help/status');
      setHelpStatus(response);
    } catch (error) {
      logger.error('Error fetching help status:', error);
      setHelpStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const checkIndexingStatus = useCallback(async () => {
    try {
      const response = await apiGet<IndexingStatus>('/api/help/index-status');
      setIndexingStatus(response);

      if (response.is_indexing) {
        setIndexing(true);
        // Also refresh the main status to show live doc/chunk counts
        fetchHelpStatus();
        // Start polling if indexing is in progress
        if (!pollIntervalRef.current) {
          pollIntervalRef.current = setInterval(checkIndexingStatus, 2000);
        }
      } else {
        setIndexing(false);
        // Stop polling
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }

        // Show completion message if we were polling
        if (response.status === 'completed' && response.result) {
          setMessage({
            type: 'success',
            text: `Indexing complete: ${response.result.total_documents} docs, ${response.result.total_chunks} chunks`
          });
          // Refresh the main status
          fetchHelpStatus();
        } else if (response.status === 'error' && response.error) {
          setMessage({
            type: 'error',
            text: `Indexing failed: ${response.error}`
          });
        }
      }
    } catch (error) {
      logger.error('Error checking indexing status:', error);
    }
  }, []);

  const handleReindex = async (force: boolean = false) => {
    setIndexing(true);
    setMessage(null);

    try {
      const response = await apiPost<{
        status: string;
        message: string;
        started_at?: string;
      }>(`/api/help/index-docs?force=${force}`, {});

      if (response.status === 'started') {
        // Start polling for progress
        setMessage({
          type: 'success',
          text: 'Indexing started in background...'
        });
        pollIntervalRef.current = setInterval(checkIndexingStatus, 2000);
      } else if (response.status === 'already_running') {
        setMessage({
          type: 'success',
          text: 'Indexing is already in progress'
        });
        // Start polling if not already
        if (!pollIntervalRef.current) {
          pollIntervalRef.current = setInterval(checkIndexingStatus, 2000);
        }
      }
    } catch (error: unknown) {
      logger.error('Error starting indexing:', error);
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to start indexing'
      });
      setIndexing(false);
    }
  };

  // Calculate elapsed time for display
  const getElapsedTime = () => {
    if (!indexingStatus?.started_at) return '';
    // Parse the ISO timestamp and ensure we're comparing UTC times
    const started = new Date(indexingStatus.started_at + (indexingStatus.started_at.endsWith('Z') ? '' : 'Z'));
    const now = new Date();
    const seconds = Math.max(0, Math.floor((now.getTime() - started.getTime()) / 1000));
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-6">Help System</h3>
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </div>
    );
  }

  const isHealthy = helpStatus && helpStatus.total_documents > 0 && helpStatus.total_chunks > 0;

  // Calculate admin and user stats from categories or by_role
  const adminDocs = helpStatus?.by_role?.admin?.documents ?? helpStatus?.categories?.admin ?? 0;
  const adminChunks = helpStatus?.by_role?.admin?.chunks ?? 0;
  const userDocs = helpStatus?.by_role?.user?.documents ?? helpStatus?.categories?.user ?? 0;
  const userChunks = helpStatus?.by_role?.user?.chunks ?? 0;

  return (
    <div className="card p-6">
      {/* Header with Status */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${
            indexing ? 'bg-blue-500' : isHealthy ? 'bg-green-500' : 'bg-yellow-500'
          } animate-pulse`}></div>
          <div>
            <h3 className="text-lg font-semibold text-primary">Help System</h3>
            <p className="text-sm text-secondary">
              {indexing ? 'Re-indexing documentation...' : isHealthy ? 'Documentation indexed' : 'Documentation needs indexing'}
            </p>
          </div>
        </div>

        {/* Reindex Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => handleReindex(false)}
            disabled={indexing}
            className="px-3 py-1.5 text-sm font-medium rounded-lg bg-subtle hover:bg-hover text-primary transition-colors disabled:opacity-50"
            title="Index new documents only"
          >
            {indexing ? <LoadingSpinner size="sm" /> : 'Update Index'}
          </button>
          <button
            onClick={() => handleReindex(true)}
            disabled={indexing}
            className="px-3 py-1.5 text-sm font-medium rounded-lg bg-primary text-white hover:opacity-90 transition-colors disabled:opacity-50"
            title="Force reindex all documents"
          >
            {indexing ? <LoadingSpinner size="sm" /> : 'Reindex All'}
          </button>
        </div>
      </div>

      {/* Progress Bar (shown during indexing) */}
      {indexing && indexingStatus && (
        <div className="mb-4 p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-400">
              {indexingStatus.progress > 0 && indexingStatus.progress < 100
                ? `${indexingStatus.progress}% complete`
                : indexingStatus.total_files > 0
                  ? `Indexing ${indexingStatus.total_files} files`
                  : 'Starting...'}
            </span>
            <span className="text-xs text-blue-300">{getElapsedTime()}</span>
          </div>
          <div className="w-full bg-blue-900/30 rounded-full h-2 overflow-hidden">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
              style={{
                width: indexingStatus.progress > 0
                  ? `${Math.min(indexingStatus.progress, 100)}%`
                  : '5%',
              }}
            />
          </div>
          <p className="mt-2 text-xs text-blue-300/70">
            {indexingStatus.current_file
              ? `Processing: ${indexingStatus.current_file}`
              : 'Processing documentation and generating embeddings...'}
          </p>
        </div>
      )}

      {/* Status Message */}
      {message && !indexing && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${
          message.type === 'success'
            ? 'bg-green-500/10 text-green-400 border border-green-500/20'
            : 'bg-red-500/10 text-red-400 border border-red-500/20'
        }`}>
          {message.text}
        </div>
      )}

      {/* Admin and User Help Side by Side */}
      {helpStatus && (
        <div className="grid grid-cols-2 gap-6">
          {/* Admin Help */}
          <div className="p-4 rounded-lg bg-subtle border border-default">
            <div className="flex items-center gap-2 mb-4">
              <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <h4 className="font-semibold text-primary">Admin Help</h4>
            </div>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-purple-400">{adminDocs}</div>
                <div className="text-xs text-secondary">Documents</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-300">{adminChunks}</div>
                <div className="text-xs text-secondary">Chunks</div>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-default">
              <div className={`text-xs font-medium ${adminDocs > 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                {adminDocs > 0 ? 'Indexed' : 'Not indexed'}
              </div>
            </div>
          </div>

          {/* User Help */}
          <div className="p-4 rounded-lg bg-subtle border border-default">
            <div className="flex items-center gap-2 mb-4">
              <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              <h4 className="font-semibold text-primary">User Help</h4>
            </div>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-400">{userDocs}</div>
                <div className="text-xs text-secondary">Documents</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-300">{userChunks}</div>
                <div className="text-xs text-secondary">Chunks</div>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-default">
              <div className={`text-xs font-medium ${userDocs > 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                {userDocs > 0 ? 'Indexed' : 'Not indexed'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Total Stats */}
      {helpStatus && (
        <div className="mt-4 pt-4 border-t border-default">
          <div className="flex items-center justify-between text-sm">
            <span className="text-secondary">Total:</span>
            <span className="text-primary font-medium">
              {helpStatus.total_documents} documents, {helpStatus.total_chunks} chunks
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
