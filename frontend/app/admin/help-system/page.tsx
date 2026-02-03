'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiGet, apiPost, apiPut } from '@/lib/api';
import { logger } from '@/lib/logger';

interface HelpDocument {
  id: string;
  title: string;
  file_path: string;
  category: string;
  created_at: string;
  updated_at: string;
  chunk_count: number;
  content?: string;
}

interface HelpDocumentDetail {
  id: string;
  title: string;
  file_path: string;
  category: string;
  content: string;
  created_at: string;
  updated_at: string;
  chunk_count: number;
}

interface UpdateDocumentResponse {
  success: boolean;
  document_id: string;
  title: string;
  word_count: number;
  chunks_created: number;
}

interface HelpDocsResponse {
  success: boolean;
  documents: {
    user: HelpDocument[];
    admin: HelpDocument[];
  };
  total_count: number;
}

interface ReindexResponse {
  success: boolean;
  document_id: string;
  title: string;
  chunks_created: number;
}

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

interface HelpAnalytics {
  success: boolean;
  period_days: number;
  summary: {
    total_questions: number;
    total_responses: number;
    avg_confidence: number;
    low_confidence_count: number;
    feedback_rate: number;
    health_status: 'healthy' | 'warning' | 'critical';
  };
  feedback: {
    positive: number;
    negative: number;
    no_feedback: number;
  };
  low_confidence_responses: Array<{
    id: string;
    conversation_id: string;
    conversation_title: string;
    help_type: 'admin' | 'user';
    response_preview: string;
    avg_similarity: number;
    source_count: number;
    sources: Array<{ title: string; section: string; similarity: number }>;
    timestamp: string;
    feedback: number | null;
  }>;
  recent_questions: Array<{
    id: string;
    conversation_id: string;
    question: string;
    timestamp: string;
  }>;
}

export default function HelpSystemPage() {
  const [activeTab, setActiveTab] = useState<'status' | 'documents' | 'analytics'>('status');
  const [documents, setDocuments] = useState<HelpDocsResponse | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [docsError, setDocsError] = useState<string | null>(null);
  const [reindexingDoc, setReindexingDoc] = useState<string | null>(null);

  // Status tab state
  const [helpStatus, setHelpStatus] = useState<HelpStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  // Indexing state (for Documents tab)
  const [indexing, setIndexing] = useState(false);
  const [indexingStatus, setIndexingStatus] = useState<IndexingStatus | null>(null);
  const [indexMessage, setIndexMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Analytics state
  const [analytics, setAnalytics] = useState<HelpAnalytics | null>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [analyticsDays, setAnalyticsDays] = useState(30);
  const [exporting, setExporting] = useState(false);

  // Edit document state
  const [editingDoc, setEditingDoc] = useState<HelpDocumentDetail | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [loadingEdit, setLoadingEdit] = useState(false);
  const [savingDoc, setSavingDoc] = useState(false);

  useEffect(() => {
    // Always fetch status on load
    fetchHelpStatus();
    checkIndexingStatus();

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount-only effect
  }, []);

  useEffect(() => {
    if (activeTab === 'documents' && !documents) {
      fetchDocuments();
    }
    if (activeTab === 'analytics' && !analytics) {
      fetchAnalytics();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fetch functions are stable
  }, [activeTab, documents, analytics]);

  const fetchHelpStatus = async () => {
    try {
      const response = await apiGet<HelpStatus>('/api/help/status');
      setHelpStatus(response);
    } catch (error) {
      logger.error('Error fetching help status:', error);
      setHelpStatus(null);
    } finally {
      setLoadingStatus(false);
    }
  };

  const checkIndexingStatus = useCallback(async () => {
    try {
      const response = await apiGet<IndexingStatus>('/api/help/index-status');
      setIndexingStatus(response);

      if (response.is_indexing) {
        setIndexing(true);
        fetchHelpStatus();
        if (!pollIntervalRef.current) {
          pollIntervalRef.current = setInterval(checkIndexingStatus, 2000);
        }
      } else {
        setIndexing(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }

        if (response.status === 'completed' && response.result) {
          setIndexMessage({
            type: 'success',
            text: `Indexing complete: ${response.result.total_documents} docs, ${response.result.total_chunks} chunks`
          });
          fetchHelpStatus();
          fetchDocuments();
        } else if (response.status === 'error' && response.error) {
          setIndexMessage({
            type: 'error',
            text: `Indexing failed: ${response.error}`
          });
        }
      }
    } catch (error) {
      logger.error('Error checking indexing status:', error);
    }
  }, []);

  const handleBulkReindex = async (force: boolean = false) => {
    setIndexing(true);
    setIndexMessage(null);

    try {
      const response = await apiPost<{
        status: string;
        message: string;
        started_at?: string;
      }>(`/api/help/index-docs?force=${force}`, {});

      if (response.status === 'started') {
        setIndexMessage({
          type: 'success',
          text: 'Indexing started in background...'
        });
        pollIntervalRef.current = setInterval(checkIndexingStatus, 2000);
      } else if (response.status === 'already_running') {
        setIndexMessage({
          type: 'success',
          text: 'Indexing is already in progress'
        });
        if (!pollIntervalRef.current) {
          pollIntervalRef.current = setInterval(checkIndexingStatus, 2000);
        }
      }
    } catch (error: unknown) {
      logger.error('Error starting indexing:', error);
      setIndexMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to start indexing'
      });
      setIndexing(false);
    }
  };

  const getElapsedTime = () => {
    if (!indexingStatus?.started_at) return '';
    const started = new Date(indexingStatus.started_at + (indexingStatus.started_at.endsWith('Z') ? '' : 'Z'));
    const now = new Date();
    const seconds = Math.max(0, Math.floor((now.getTime() - started.getTime()) / 1000));
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    setDocsError(null);
    try {
      const data = await apiGet<HelpDocsResponse>('/api/admin/help-documents');
      setDocuments(data);
    } catch (err) {
      logger.error('Error fetching help documents:', err);
      setDocsError('Failed to load help documents');
    } finally {
      setLoadingDocs(false);
    }
  };

  const fetchAnalytics = async () => {
    setLoadingAnalytics(true);
    setAnalyticsError(null);
    try {
      const data = await apiGet<HelpAnalytics>(`/api/admin/help-analytics?days=${analyticsDays}`);
      setAnalytics(data);
    } catch (err) {
      logger.error('Error fetching help analytics:', err);
      setAnalyticsError('Failed to load help analytics');
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const handleExportConversations = async () => {
    setExporting(true);
    try {
      const data = await apiGet<{
        success: boolean;
        count: number;
        period_days: number;
        conversations: Array<{
          id: string;
          title: string;
          help_type: string;
          user_email: string;
          user_name: string;
          created_at: string;
          message_count: number;
          messages: Array<{
            id: string;
            role: string;
            content: string;
            sources: unknown;
            feedback: number | null;
            timestamp: string;
          }>;
        }>;
      }>(`/api/admin/help-conversations/export?days=${analyticsDays}`);

      if (data.success && data.conversations.length > 0) {
        // Create downloadable JSON file
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `help-conversations-${analyticsDays}days-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast.success(`Exported ${data.count} conversations`);
      } else {
        toast.error('No conversations to export');
      }
    } catch (err) {
      logger.error('Error exporting conversations:', err);
      toast.error('Failed to export conversations');
    } finally {
      setExporting(false);
    }
  };

  const handleReindexDocument = async (docId: string, docTitle: string) => {
    setReindexingDoc(docId);
    try {
      const response = await apiPost<ReindexResponse>(`/api/admin/help-documents/${docId}/reindex`, {});
      if (response.success) {
        toast.success(`Reindexed "${docTitle}" (${response.chunks_created} chunks)`);
        fetchDocuments();
      }
    } catch (err) {
      logger.error('Error reindexing document:', err);
      toast.error(`Failed to reindex "${docTitle}"`);
    } finally {
      setReindexingDoc(null);
    }
  };

  const handleOpenEditDocument = async (docId: string) => {
    setLoadingEdit(true);
    try {
      const response = await apiGet<{ success: boolean; document: HelpDocumentDetail }>(
        `/api/admin/help-documents/${docId}`
      );
      if (response.success) {
        setEditingDoc(response.document);
        setEditTitle(response.document.title);
        setEditContent(response.document.content);
      }
    } catch (err) {
      logger.error('Error loading document for edit:', err);
      toast.error('Failed to load document');
    } finally {
      setLoadingEdit(false);
    }
  };

  const handleCloseEdit = () => {
    setEditingDoc(null);
    setEditTitle('');
    setEditContent('');
  };

  const handleSaveDocument = async () => {
    if (!editingDoc) return;

    if (editTitle.trim().length < 3) {
      toast.error('Title must be at least 3 characters');
      return;
    }

    if (editContent.trim().length < 50) {
      toast.error('Content must be at least 50 characters');
      return;
    }

    setSavingDoc(true);
    try {
      const response = await apiPut<UpdateDocumentResponse>(
        `/api/admin/help-documents/${editingDoc.id}`,
        { title: editTitle, content: editContent }
      );

      if (response.success) {
        toast.success(`Saved and reindexed "${response.title}" (${response.chunks_created} chunks)`);
        handleCloseEdit();
        fetchDocuments();
        fetchHelpStatus();
      }
    } catch (err) {
      logger.error('Error saving document:', err);
      toast.error('Failed to save document');
    } finally {
      setSavingDoc(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isHealthy = helpStatus && helpStatus.total_documents > 0 && helpStatus.total_chunks > 0;
  const adminDocs = helpStatus?.by_role?.admin?.documents ?? helpStatus?.categories?.admin ?? 0;
  const adminChunks = helpStatus?.by_role?.admin?.chunks ?? 0;
  const userDocs = helpStatus?.by_role?.user?.documents ?? helpStatus?.categories?.user ?? 0;
  const userChunks = helpStatus?.by_role?.user?.chunks ?? 0;

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.7) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-8">
      {/* Help System Header */}
      <div>
        <h1 className="text-3xl font-bold text-primary">Help Documentation System</h1>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab('status')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'status'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          System Status
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'documents'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Documents
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'analytics'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Analytics
        </button>
      </div>

      {activeTab === 'status' ? (
        <>
          {/* Status Panel - Read Only */}
          <div className="card p-6">
            {loadingStatus ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="md" />
              </div>
            ) : (
              <>
                {/* Header with Status */}
                <div className="flex items-center gap-3 mb-6">
                  <div className={`w-3 h-3 rounded-full ${
                    indexing ? 'bg-blue-500' : isHealthy ? 'bg-green-500' : 'bg-yellow-500'
                  } animate-pulse`}></div>
                  <div>
                    <h3 className="text-lg font-semibold text-primary">Help System</h3>
                    <p className="text-sm text-secondary">
                      {indexing ? 'Re-indexing documentation...' : isHealthy ? 'Documentation indexed and operational' : 'Documentation needs indexing'}
                    </p>
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
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-secondary">Total:</span>
                      <span className="text-primary font-medium">
                        {helpStatus.total_documents} documents, {helpStatus.total_chunks} chunks
                      </span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Help System Info */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-primary mb-4">How the Help System Works</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 rounded-lg bg-subtle border border-default">
                <h4 className="font-medium text-primary mb-2">Documentation</h4>
                <p className="text-sm text-secondary">
                  Markdown files in <code className="text-xs bg-hover px-1 rounded">docs/help/</code> are parsed into chunks for semantic search.
                </p>
              </div>
              <div className="p-4 rounded-lg bg-subtle border border-default">
                <h4 className="font-medium text-primary mb-2">Vector Search</h4>
                <p className="text-sm text-secondary">
                  Each chunk is embedded using Voyage AI and stored in the database for fast semantic similarity search.
                </p>
              </div>
              <div className="p-4 rounded-lg bg-subtle border border-default">
                <h4 className="font-medium text-primary mb-2">AI Responses</h4>
                <p className="text-sm text-secondary">
                  User questions retrieve relevant chunks, which are passed to the LLM to generate accurate, sourced answers.
                </p>
              </div>
            </div>
          </div>
        </>
      ) : activeTab === 'documents' ? (
        <div className="space-y-8">
          {/* Bulk Indexing Controls */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-primary mb-4">Index Documentation</h3>
            <p className="text-sm text-secondary mb-4">
              Index help documentation from markdown files. Choose to scan for new documents only or force a complete reindex.
            </p>

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
            {indexMessage && !indexing && (
              <div className={`mb-4 p-3 rounded-lg text-sm ${
                indexMessage.type === 'success'
                  ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                  : 'bg-red-500/10 text-red-400 border border-red-500/20'
              }`}>
                {indexMessage.text}
              </div>
            )}

            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[200px]">
                <button
                  onClick={() => handleBulkReindex(false)}
                  disabled={indexing}
                  className="w-full px-4 py-3 text-sm font-medium rounded-lg bg-subtle hover:bg-hover text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-default"
                >
                  {indexing ? (
                    <span className="flex items-center justify-center gap-2">
                      <LoadingSpinner size="sm" />
                      Indexing...
                    </span>
                  ) : (
                    'Scan for New Documents'
                  )}
                </button>
                <p className="mt-2 text-xs text-muted">
                  Quickly scans for new markdown files and indexes only documents that haven&apos;t been indexed yet. Use this after adding new documentation.
                </p>
              </div>
              <div className="flex-1 min-w-[200px]">
                <button
                  onClick={() => handleBulkReindex(true)}
                  disabled={indexing}
                  className="w-full px-4 py-3 text-sm font-medium rounded-lg bg-primary text-white hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {indexing ? (
                    <span className="flex items-center justify-center gap-2">
                      <LoadingSpinner size="sm" />
                      Indexing...
                    </span>
                  ) : (
                    'Reindex All Documents'
                  )}
                </button>
                <p className="mt-2 text-xs text-muted">
                  Deletes all existing chunks and regenerates embeddings for every document. Use this after updating documentation content or if search results seem stale.
                </p>
              </div>
            </div>
          </div>

          {loadingDocs ? (
            <div className="card p-12 flex justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : docsError ? (
            <div className="card p-6 text-center text-red-500">{docsError}</div>
          ) : documents ? (
            <>
              {/* User Documentation */}
              <div className="card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-lg font-semibold text-primary">User Documentation</h3>
                  <span className="badge-primary ml-2">{documents.documents.user.length} docs</span>
                </div>
                <p className="text-sm text-secondary mb-4">
                  Documentation available to all users in the help chat.
                </p>
                {documents.documents.user.length === 0 ? (
                  <p className="text-muted text-sm">No user documentation indexed yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-page border-b border-default">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Title</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">File Path</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Chunks</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Last Indexed</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-default">
                        {documents.documents.user.map((doc) => (
                          <tr key={doc.id} className="hover:bg-hover transition-colors">
                            <td className="px-4 py-3 text-sm font-medium text-primary">{doc.title}</td>
                            <td className="px-4 py-3 text-sm text-muted font-mono text-xs">{doc.file_path}</td>
                            <td className="px-4 py-3 text-sm text-secondary">{doc.chunk_count}</td>
                            <td className="px-4 py-3 text-sm text-muted">{formatDate(doc.updated_at)}</td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex items-center justify-end gap-3">
                                <button
                                  onClick={() => handleOpenEditDocument(doc.id)}
                                  disabled={loadingEdit}
                                  className="text-xs font-medium text-blue-400 hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Edit this document"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => handleReindexDocument(doc.id, doc.title)}
                                  disabled={reindexingDoc === doc.id}
                                  className="text-xs font-medium text-blue-400 hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Reindex this document"
                                >
                                  {reindexingDoc === doc.id ? (
                                    <span className="flex items-center gap-1">
                                      <LoadingSpinner size="sm" />
                                      Reindexing...
                                    </span>
                                  ) : (
                                    'Reindex'
                                  )}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Admin Documentation */}
              <div className="card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-lg font-semibold text-primary">Admin Documentation</h3>
                  <span className="badge-primary ml-2">{documents.documents.admin.length} docs</span>
                </div>
                <p className="text-sm text-secondary mb-4">
                  Documentation available only to admins in the help chat.
                </p>
                {documents.documents.admin.length === 0 ? (
                  <p className="text-muted text-sm">No admin documentation indexed yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-page border-b border-default">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Title</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">File Path</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Chunks</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Last Indexed</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-default">
                        {documents.documents.admin.map((doc) => (
                          <tr key={doc.id} className="hover:bg-hover transition-colors">
                            <td className="px-4 py-3 text-sm font-medium text-primary">{doc.title}</td>
                            <td className="px-4 py-3 text-sm text-muted font-mono text-xs">{doc.file_path}</td>
                            <td className="px-4 py-3 text-sm text-secondary">{doc.chunk_count}</td>
                            <td className="px-4 py-3 text-sm text-muted">{formatDate(doc.updated_at)}</td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex items-center justify-end gap-3">
                                <button
                                  onClick={() => handleOpenEditDocument(doc.id)}
                                  disabled={loadingEdit}
                                  className="text-xs font-medium text-blue-400 hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Edit this document"
                                >
                                  Edit
                                </button>
                                <button
                                  onClick={() => handleReindexDocument(doc.id, doc.title)}
                                  disabled={reindexingDoc === doc.id}
                                  className="text-xs font-medium text-blue-400 hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Reindex this document"
                                >
                                  {reindexingDoc === doc.id ? (
                                    <span className="flex items-center gap-1">
                                      <LoadingSpinner size="sm" />
                                      Reindexing...
                                    </span>
                                  ) : (
                                    'Reindex'
                                  )}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Refresh Button */}
              <div className="flex justify-end">
                <button
                  onClick={fetchDocuments}
                  className="btn-secondary flex items-center gap-2"
                  disabled={loadingDocs}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>
            </>
          ) : null}
        </div>
      ) : (
        /* Analytics Tab */
        <div className="space-y-8">
          {/* Period Selector */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-primary">Help System Analytics</h3>
                <p className="text-sm text-secondary">
                  Analyze questions asked, response confidence, and user feedback to identify documentation gaps.
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label htmlFor="days" className="text-sm text-secondary">Period:</label>
                  <select
                    id="days"
                    value={analyticsDays}
                    onChange={(e) => {
                      setAnalyticsDays(Number(e.target.value));
                      setAnalytics(null); // Reset to trigger refetch
                    }}
                    className="px-3 py-1.5 text-sm rounded-lg bg-subtle border border-default text-primary"
                  >
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                    <option value={60}>Last 60 days</option>
                    <option value={90}>Last 90 days</option>
                  </select>
                </div>
                <button
                  onClick={handleExportConversations}
                  disabled={exporting}
                  className="flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-lg bg-subtle hover:bg-hover text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-default"
                >
                  {exporting ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Export Conversations
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {loadingAnalytics ? (
            <div className="card p-12 flex justify-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : analyticsError ? (
            <div className="card p-6 text-center text-red-500">{analyticsError}</div>
          ) : analytics ? (
            <>
              {/* Summary Stats */}
              <div className="grid grid-cols-4 gap-6">
                <div className="card p-6 text-center">
                  <div className="text-3xl font-bold text-primary">{analytics.summary.total_questions}</div>
                  <div className="text-sm text-secondary mt-1">Questions Asked</div>
                </div>
                <div className="card p-6 text-center">
                  <div className={`text-3xl font-bold ${getConfidenceColor(analytics.summary.avg_confidence)}`}>
                    {(analytics.summary.avg_confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-secondary mt-1">Avg Confidence</div>
                </div>
                <div className="card p-6 text-center">
                  <div className="text-3xl font-bold text-yellow-400">{analytics.summary.low_confidence_count}</div>
                  <div className="text-sm text-secondary mt-1">Low Confidence</div>
                </div>
                <div className="card p-6 text-center relative group">
                  <div className={`w-3 h-3 rounded-full ${getHealthStatusColor(analytics.summary.health_status)} absolute top-3 right-3`}></div>
                  <div className="text-3xl font-bold text-primary">{analytics.summary.feedback_rate}%</div>
                  <div className="text-sm text-secondary mt-1">Feedback Rate</div>
                </div>
              </div>

              {/* Feedback Breakdown */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-primary mb-4">User Feedback</h3>
                <div className="grid grid-cols-3 gap-6">
                  <div className="text-center p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                    <div className="text-2xl font-bold text-green-400">{analytics.feedback.positive}</div>
                    <div className="text-sm text-green-300 mt-1">Helpful</div>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                    <div className="text-2xl font-bold text-red-400">{analytics.feedback.negative}</div>
                    <div className="text-sm text-red-300 mt-1">Not Helpful</div>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-gray-500/10 border border-gray-500/20">
                    <div className="text-2xl font-bold text-gray-400">{analytics.feedback.no_feedback}</div>
                    <div className="text-sm text-gray-300 mt-1">No Feedback</div>
                  </div>
                </div>
              </div>

              {/* Low Confidence Responses */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-primary mb-2">Low Confidence Responses</h3>
                <p className="text-sm text-secondary mb-4">
                  Responses where source documents had low similarity scores (&lt;75%). These indicate potential gaps in documentation coverage.
                </p>
                {analytics.low_confidence_responses.length === 0 ? (
                  <div className="text-center py-8 text-muted">
                    No low confidence responses in this period.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-page border-b border-default">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Question</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Context</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Confidence</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Sources</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Feedback</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">Date</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-default">
                        {analytics.low_confidence_responses.map((response) => (
                          <tr key={response.id} className="hover:bg-hover transition-colors">
                            <td className="px-4 py-3 text-sm text-primary max-w-xs">
                              <div className="truncate" title={response.conversation_title}>
                                {response.conversation_title}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                response.help_type === 'admin'
                                  ? 'bg-purple-500/20 text-purple-400'
                                  : 'bg-blue-500/20 text-blue-400'
                              }`}>
                                {response.help_type === 'admin' ? 'Admin' : 'User'}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`text-sm font-medium ${getConfidenceColor(response.avg_similarity)}`}>
                                {(response.avg_similarity * 100).toFixed(0)}%
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-secondary">
                              {response.source_count} sources
                            </td>
                            <td className="px-4 py-3">
                              {response.feedback === 1 ? (
                                <span className="text-green-400">Helpful</span>
                              ) : response.feedback === -1 ? (
                                <span className="text-red-400">Not Helpful</span>
                              ) : (
                                <span className="text-muted">None</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-muted">
                              {formatDate(response.timestamp)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Recent Questions */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-primary mb-2">Recent Questions</h3>
                <p className="text-sm text-secondary mb-4">
                  Most recent questions asked to the help system. Review these to understand what users are looking for.
                </p>
                {analytics.recent_questions.length === 0 ? (
                  <div className="text-center py-8 text-muted">
                    No questions in this period.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {analytics.recent_questions.map((question) => (
                      <div key={question.id} className="p-3 rounded-lg bg-subtle border border-default">
                        <p className="text-sm text-primary">{question.question}</p>
                        <p className="text-xs text-muted mt-1">{formatDate(question.timestamp)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Refresh Button */}
              <div className="flex justify-end">
                <button
                  onClick={fetchAnalytics}
                  className="btn-secondary flex items-center gap-2"
                  disabled={loadingAnalytics}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Edit Document Modal */}
      {editingDoc && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-page rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-default">
              <div>
                <h2 className="text-lg font-semibold text-primary">Edit Document</h2>
                <p className="text-sm text-muted">{editingDoc.file_path}</p>
              </div>
              <button
                onClick={handleCloseEdit}
                className="p-2 hover:bg-hover rounded-lg transition-colors"
                disabled={savingDoc}
              >
                <svg className="w-5 h-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Title Input */}
              <div>
                <label htmlFor="edit-title" className="block text-sm font-medium text-secondary mb-1">
                  Title
                </label>
                <input
                  id="edit-title"
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-subtle border border-default text-primary focus:outline-none focus:ring-2 focus:ring-primary/50"
                  placeholder="Document title"
                  disabled={savingDoc}
                />
              </div>

              {/* Content Textarea */}
              <div className="flex-1">
                <label htmlFor="edit-content" className="block text-sm font-medium text-secondary mb-1">
                  Content (Markdown)
                </label>
                <textarea
                  id="edit-content"
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full h-96 px-3 py-2 rounded-lg bg-subtle border border-default text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                  placeholder="Write markdown content here..."
                  disabled={savingDoc}
                />
                <p className="mt-1 text-xs text-muted">
                  {editContent.split(/\s+/).filter(Boolean).length} words
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-4 border-t border-default bg-subtle">
              <p className="text-xs text-muted">
                Changes will be saved and the document will be automatically reindexed.
              </p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleCloseEdit}
                  className="px-4 py-2 text-sm font-medium rounded-lg bg-hover text-secondary hover:bg-hover/80 transition-colors"
                  disabled={savingDoc}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveDocument}
                  disabled={savingDoc || editTitle.trim().length < 3 || editContent.trim().length < 50}
                  className="px-4 py-2 text-sm font-medium rounded-lg bg-primary text-white hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {savingDoc ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Saving & Reindexing...
                    </>
                  ) : (
                    'Save & Reindex'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay when opening edit */}
      {loadingEdit && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-page rounded-lg p-6 flex items-center gap-3">
            <LoadingSpinner size="md" />
            <span className="text-primary">Loading document...</span>
          </div>
        </div>
      )}
    </div>
  );
}
