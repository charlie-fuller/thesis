'use client';

/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import LoadingSpinner from '@/components/LoadingSpinner';
import { apiGet, apiPost, apiDelete, authenticatedFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

// ============================================================================
// Type Definitions
// ============================================================================

interface SystemInstructionVersion {
  id: string;
  version_number: string;
  content: string;
  file_size: number;
  status: string;
  is_active: boolean;
  version_notes: string | null;
  created_by: string | null;
  activated_by: string | null;
  created_by_name?: string;
  activated_by_name?: string;
  created_at: string;
  activated_at: string | null;
  updated_at: string;
  conversation_count?: number;
}

interface VersionListResponse {
  success: boolean;
  versions: SystemInstructionVersion[];
  total: number;
  limit: number;
  offset: number;
}

interface VersionResponse {
  success: boolean;
  version: SystemInstructionVersion;
  message?: string;
}

interface CompareResponse {
  success: boolean;
  version_a: { id: string; version_number: string; created_at: string };
  version_b: { id: string; version_number: string; created_at: string };
  diff: string[];
  stats: {
    additions: number;
    deletions: number;
    total_changes: number;
  };
}

interface SummaryResponse {
  success: boolean;
  version_a: { id: string; version_number: string; created_at: string };
  version_b: { id: string; version_number: string; created_at: string };
  summary: string;
  stats: {
    additions: number;
    deletions: number;
    total_changes: number;
  };
}

// ============================================================================
// Main Component
// ============================================================================

export default function SystemInstructionsPage() {
  // Tab state
  const [activeTab, setActiveTab] = useState<'active' | 'history' | 'upload' | 'compare'>('active');

  // Active version state
  const [activeVersion, setActiveVersion] = useState<SystemInstructionVersion | null>(null);
  const [loadingActive, setLoadingActive] = useState(true);

  // Version history state
  const [versions, setVersions] = useState<SystemInstructionVersion[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [totalVersions, setTotalVersions] = useState(0);

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadVersionNumber, setUploadVersionNumber] = useState('');
  const [uploadNotes, setUploadNotes] = useState('');
  const [uploadPreview, setUploadPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // Compare state
  const [compareVersionA, setCompareVersionA] = useState<string>('');
  const [compareVersionB, setCompareVersionB] = useState<string>('');
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [summaryResult, setSummaryResult] = useState<SummaryResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [generatingSummary, setGeneratingSummary] = useState(false);

  // Action states
  const [activating, setActivating] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  // View version modal
  const [viewingVersion, setViewingVersion] = useState<SystemInstructionVersion | null>(null);

  // ============================================================================
  // Data Fetching
  // ============================================================================

  const fetchActiveVersion = useCallback(async () => {
    setLoadingActive(true);
    try {
      const response = await apiGet<VersionResponse>('/api/admin/system-instructions/versions/active');
      if (response.success) {
        setActiveVersion(response.version);
      }
    } catch (err) {
      logger.error('Error fetching active version:', err);
      // Don't show error toast - might be first time setup with no active version
      setActiveVersion(null);
    } finally {
      setLoadingActive(false);
    }
  }, []);

  const fetchVersions = useCallback(async () => {
    setLoadingVersions(true);
    try {
      const response = await apiGet<VersionListResponse>('/api/admin/system-instructions/versions?limit=50');
      if (response.success) {
        setVersions(response.versions);
        setTotalVersions(response.total);
      }
    } catch (err) {
      logger.error('Error fetching versions:', err);
      toast.error('Failed to load version history');
    } finally {
      setLoadingVersions(false);
    }
  }, []);

  useEffect(() => {
    fetchActiveVersion();
    fetchVersions();
  }, [fetchActiveVersion, fetchVersions]);

  // ============================================================================
  // File Upload Handling
  // ============================================================================

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate extension
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'txt' && ext !== 'xml') {
      toast.error('Only .txt and .xml files are allowed');
      return;
    }

    // Validate size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 50MB');
      return;
    }

    setUploadFile(file);

    // Read file for preview
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setUploadPreview(content);
    };
    reader.readAsText(file);
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }

    if (!uploadVersionNumber.trim()) {
      toast.error('Please enter a version number');
      return;
    }

    // Validate version number format
    const versionPattern = /^[0-9]+\.[0-9]+(-.+)?$/;
    if (!versionPattern.test(uploadVersionNumber)) {
      toast.error('Invalid version number format. Use format like "1.4" or "2.0-beta"');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('version_number', uploadVersionNumber);
      if (uploadNotes) {
        formData.append('version_notes', uploadNotes);
      }

      const response = await authenticatedFetch('/api/admin/system-instructions/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      toast.success(`Version ${uploadVersionNumber} created successfully`);

      // Reset form
      setUploadFile(null);
      setUploadVersionNumber('');
      setUploadNotes('');
      setUploadPreview(null);

      // Refresh data
      fetchVersions();

      // Switch to history tab to see the new version
      setActiveTab('history');

    } catch (err) {
      logger.error('Upload error:', err);
      toast.error(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  // ============================================================================
  // Version Actions
  // ============================================================================

  const handleActivateVersion = async (versionId: string) => {
    if (!confirm('Are you sure you want to activate this version? All new chats will use this version.')) {
      return;
    }

    setActivating(versionId);
    try {
      const response = await apiPost<VersionResponse>(
        `/api/admin/system-instructions/versions/${versionId}/activate`,
        {}
      );

      if (response.success) {
        toast.success(response.message || 'Version activated');
        fetchActiveVersion();
        fetchVersions();
      }
    } catch (err) {
      logger.error('Activation error:', err);
      toast.error('Failed to activate version');
    } finally {
      setActivating(null);
    }
  };

  const handleDeleteVersion = async (version: SystemInstructionVersion) => {
    if (version.is_active) {
      toast.error('Cannot delete the active version');
      return;
    }

    if (!confirm(`Are you sure you want to delete version ${version.version_number}? This cannot be undone.`)) {
      return;
    }

    setDeleting(version.id);
    try {
      const response = await apiDelete<{ success: boolean; message: string }>(
        `/api/admin/system-instructions/versions/${version.id}`
      );

      if (response.success) {
        toast.success(response.message || 'Version deleted');
        fetchVersions();
      }
    } catch (err: unknown) {
      logger.error('Delete error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete version';
      toast.error(errorMessage);
    } finally {
      setDeleting(null);
    }
  };

  const handleViewVersion = async (versionId: string) => {
    try {
      const response = await apiGet<VersionResponse>(
        `/api/admin/system-instructions/versions/${versionId}`
      );

      if (response.success) {
        setViewingVersion(response.version);
      }
    } catch (err) {
      logger.error('Error loading version:', err);
      toast.error('Failed to load version details');
    }
  };

  // ============================================================================
  // Version Comparison
  // ============================================================================

  const handleCompare = async () => {
    if (!compareVersionA || !compareVersionB) {
      toast.error('Please select two versions to compare');
      return;
    }

    if (compareVersionA === compareVersionB) {
      toast.error('Please select two different versions');
      return;
    }

    setComparing(true);
    setCompareResult(null);
    setSummaryResult(null);

    try {
      const response = await apiPost<CompareResponse>(
        '/api/admin/system-instructions/versions/compare',
        {
          version_a_id: compareVersionA,
          version_b_id: compareVersionB,
        }
      );

      if (response.success) {
        setCompareResult(response);
      }
    } catch (err) {
      logger.error('Compare error:', err);
      toast.error('Failed to compare versions');
    } finally {
      setComparing(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!compareVersionA || !compareVersionB) {
      toast.error('Please select two versions first');
      return;
    }

    setGeneratingSummary(true);

    try {
      const response = await apiPost<SummaryResponse>(
        '/api/admin/system-instructions/versions/compare/summary',
        {
          version_a_id: compareVersionA,
          version_b_id: compareVersionB,
        }
      );

      if (response.success) {
        setSummaryResult(response);
      }
    } catch (err) {
      logger.error('Summary generation error:', err);
      toast.error('Failed to generate AI summary');
    } finally {
      setGeneratingSummary(false);
    }
  };

  // ============================================================================
  // Helpers
  // ============================================================================

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-primary">System Instructions</h1>
        <p className="text-secondary mt-2">
          Manage and version global system instructions for the AI assistant.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab('active')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'active'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Active Version
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Version History
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'upload'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Upload New
        </button>
        <button
          onClick={() => setActiveTab('compare')}
          className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'compare'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-primary'
          }`}
        >
          Compare Versions
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'active' && (
        <ActiveVersionTab
          version={activeVersion}
          loading={loadingActive}
          formatDate={formatDate}
          formatFileSize={formatFileSize}
        />
      )}

      {activeTab === 'history' && (
        <VersionHistoryTab
          versions={versions}
          loading={loadingVersions}
          total={totalVersions}
          activating={activating}
          deleting={deleting}
          onActivate={handleActivateVersion}
          onDelete={handleDeleteVersion}
          onView={handleViewVersion}
          formatDate={formatDate}
          formatFileSize={formatFileSize}
        />
      )}

      {activeTab === 'upload' && (
        <UploadTab
          file={uploadFile}
          versionNumber={uploadVersionNumber}
          notes={uploadNotes}
          preview={uploadPreview}
          uploading={uploading}
          onFileChange={handleFileChange}
          onVersionNumberChange={setUploadVersionNumber}
          onNotesChange={setUploadNotes}
          onUpload={handleUpload}
          onClearFile={() => {
            setUploadFile(null);
            setUploadPreview(null);
          }}
        />
      )}

      {activeTab === 'compare' && (
        <CompareTab
          versions={versions}
          versionA={compareVersionA}
          versionB={compareVersionB}
          result={compareResult}
          summaryResult={summaryResult}
          comparing={comparing}
          generatingSummary={generatingSummary}
          onVersionAChange={setCompareVersionA}
          onVersionBChange={setCompareVersionB}
          onCompare={handleCompare}
          onGenerateSummary={handleGenerateSummary}
        />
      )}

      {/* View Version Modal */}
      {viewingVersion && (
        <ViewVersionModal
          version={viewingVersion}
          onClose={() => setViewingVersion(null)}
          formatDate={formatDate}
          formatFileSize={formatFileSize}
        />
      )}
    </div>
  );
}

// ============================================================================
// Tab Components
// ============================================================================

interface ActiveVersionTabProps {
  version: SystemInstructionVersion | null;
  loading: boolean;
  formatDate: (date: string | null) => string;
  formatFileSize: (bytes: number) => string;
}

function ActiveVersionTab({ version, loading, formatDate, formatFileSize }: ActiveVersionTabProps) {
  if (loading) {
    return (
      <div className="card p-8 flex justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!version) {
    return (
      <div className="card p-8 text-center">
        <p className="text-secondary">No active version found.</p>
        <p className="text-muted mt-2">Upload a new version and activate it to get started.</p>
      </div>
    );
  }

  const wordCount = version.content.split(/\s+/).filter(Boolean).length;
  const charCount = version.content.length;

  return (
    <div className="space-y-6">
      {/* Version Info Card */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></div>
            <h2 className="text-xl font-semibold text-primary">
              Version {version.version_number}
            </h2>
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-500/20 text-green-400">
              Active
            </span>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-3 rounded-lg bg-subtle">
            <p className="text-xs text-muted uppercase tracking-wide">File Size</p>
            <p className="text-lg font-semibold text-primary">{formatFileSize(version.file_size)}</p>
          </div>
          <div className="p-3 rounded-lg bg-subtle">
            <p className="text-xs text-muted uppercase tracking-wide">Word Count</p>
            <p className="text-lg font-semibold text-primary">{wordCount.toLocaleString()}</p>
          </div>
          <div className="p-3 rounded-lg bg-subtle">
            <p className="text-xs text-muted uppercase tracking-wide">Characters</p>
            <p className="text-lg font-semibold text-primary">{charCount.toLocaleString()}</p>
          </div>
          <div className="p-3 rounded-lg bg-subtle">
            <p className="text-xs text-muted uppercase tracking-wide">Activated</p>
            <p className="text-sm font-medium text-primary">{formatDate(version.activated_at)}</p>
          </div>
        </div>

        {/* Version Notes */}
        {version.version_notes && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">Version Notes</h3>
            <p className="text-secondary">{version.version_notes}</p>
          </div>
        )}

        {/* Content Preview */}
        <div>
          <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">Content</h3>
          <div className="max-h-96 overflow-y-auto rounded-lg bg-page border border-default p-4">
            <pre className="text-sm text-secondary whitespace-pre-wrap font-mono">
              {version.content}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

interface VersionHistoryTabProps {
  versions: SystemInstructionVersion[];
  loading: boolean;
  total: number;
  activating: string | null;
  deleting: string | null;
  onActivate: (id: string) => void;
  onDelete: (version: SystemInstructionVersion) => void;
  onView: (id: string) => void;
  formatDate: (date: string | null) => string;
  formatFileSize: (bytes: number) => string;
}

function VersionHistoryTab({
  versions,
  loading,
  total,
  activating,
  deleting,
  onActivate,
  onDelete,
  onView,
  formatDate,
  formatFileSize,
}: VersionHistoryTabProps) {
  if (loading) {
    return (
      <div className="card p-8 flex justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (versions.length === 0) {
    return (
      <div className="card p-8 text-center">
        <p className="text-secondary">No versions found.</p>
        <p className="text-muted mt-2">Upload your first version to get started.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-6 py-4 border-b border-default">
        <h3 className="text-lg font-semibold text-primary">Version History</h3>
        <p className="text-sm text-muted">{total} version(s)</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-page border-b border-default">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                Version
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                Notes
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-default">
            {versions.map((version) => (
              <tr key={version.id} className="hover:bg-hover transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-primary">{version.version_number}</span>
                    {version.is_active && (
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-green-500/20 text-green-400">
                        Active
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    version.status === 'active'
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-gray-500/20 text-gray-400'
                  }`}>
                    {version.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-secondary">
                  {formatFileSize(version.file_size)}
                </td>
                <td className="px-6 py-4">
                  <div>
                    <p className="text-secondary text-sm">{formatDate(version.created_at)}</p>
                    {version.created_by_name && (
                      <p className="text-muted text-xs">by {version.created_by_name}</p>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-secondary text-sm max-w-xs truncate">
                    {version.version_notes || '-'}
                  </p>
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => onView(version.id)}
                      className="px-3 py-1.5 text-xs font-medium text-secondary hover:text-primary border border-default rounded-lg hover:border-focus transition-colors cursor-pointer"
                    >
                      View
                    </button>
                    {!version.is_active && (
                      <>
                        <button
                          onClick={() => onActivate(version.id)}
                          disabled={activating === version.id}
                          className="px-3 py-1.5 text-xs font-medium text-green-400 hover:text-green-300 border border-green-500/30 rounded-lg hover:border-green-500/50 transition-colors disabled:opacity-50 cursor-pointer"
                        >
                          {activating === version.id ? 'Activating...' : 'Activate'}
                        </button>
                        <button
                          onClick={() => onDelete(version)}
                          disabled={deleting === version.id}
                          className="px-3 py-1.5 text-xs font-medium text-red-400 hover:text-red-300 border border-red-500/30 rounded-lg hover:border-red-500/50 transition-colors disabled:opacity-50 cursor-pointer"
                        >
                          {deleting === version.id ? 'Deleting...' : 'Delete'}
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface UploadTabProps {
  file: File | null;
  versionNumber: string;
  notes: string;
  preview: string | null;
  uploading: boolean;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onVersionNumberChange: (value: string) => void;
  onNotesChange: (value: string) => void;
  onUpload: () => void;
  onClearFile: () => void;
}

function UploadTab({
  file,
  versionNumber,
  notes,
  preview,
  uploading,
  onFileChange,
  onVersionNumberChange,
  onNotesChange,
  onUpload,
  onClearFile,
}: UploadTabProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Upload Form */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-4">Upload New Version</h3>

        <div className="space-y-4">
          {/* Version Number */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Version Number <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={versionNumber}
              onChange={(e) => onVersionNumberChange(e.target.value)}
              placeholder="e.g., 1.4 or 2.0-beta"
              className="input-field w-full"
            />
            <p className="text-xs text-muted mt-1">
              Format: X.Y or X.Y-suffix (e.g., 1.0, 2.3, 1.0-beta)
            </p>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Instructions File <span className="text-red-400">*</span>
            </label>
            {file ? (
              <div className="flex items-center justify-between p-3 rounded-lg bg-subtle border border-default">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-secondary">{file.name}</span>
                  <span className="text-muted text-sm">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
                <button
                  onClick={onClearFile}
                  className="text-red-400 hover:text-red-300 cursor-pointer"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center p-6 rounded-lg border-2 border-dashed border-default hover:border-focus transition-colors cursor-pointer">
                <svg className="w-8 h-8 text-muted mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span className="text-secondary">Click to upload or drag and drop</span>
                <span className="text-muted text-sm">.txt or .xml files only (max 50MB)</span>
                <input
                  type="file"
                  accept=".txt,.xml"
                  onChange={onFileChange}
                  className="hidden"
                />
              </label>
            )}
          </div>

          {/* Version Notes */}
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Version Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => onNotesChange(e.target.value)}
              placeholder="Describe what changed in this version..."
              rows={4}
              className="textarea-field w-full"
            />
          </div>

          {/* Upload Button */}
          <button
            onClick={onUpload}
            disabled={!file || !versionNumber || uploading}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <LoadingSpinner size="sm" />
                Uploading...
              </span>
            ) : (
              'Upload Version'
            )}
          </button>
        </div>
      </div>

      {/* Preview Panel */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-4">Content Preview</h3>
        {preview ? (
          <div className="max-h-[500px] overflow-y-auto rounded-lg bg-page border border-default p-4">
            <pre className="text-sm text-secondary whitespace-pre-wrap font-mono">
              {preview}
            </pre>
          </div>
        ) : (
          <div className="flex items-center justify-center h-64 rounded-lg bg-subtle border border-default">
            <p className="text-muted">Upload a file to preview its content</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface CompareTabProps {
  versions: SystemInstructionVersion[];
  versionA: string;
  versionB: string;
  result: CompareResponse | null;
  summaryResult: SummaryResponse | null;
  comparing: boolean;
  generatingSummary: boolean;
  onVersionAChange: (id: string) => void;
  onVersionBChange: (id: string) => void;
  onCompare: () => void;
  onGenerateSummary: () => void;
}

interface ChangelogData {
  versionA: { changelog: string | null; filename?: string } | null;
  versionB: { changelog: string | null; filename?: string } | null;
}

function CompareTab({
  versions,
  versionA,
  versionB,
  result,
  summaryResult,
  comparing,
  generatingSummary,
  onVersionAChange,
  onVersionBChange,
  onCompare,
  onGenerateSummary,
}: CompareTabProps) {
  const [expandedPanels, setExpandedPanels] = useState<Record<string, boolean>>({
    summary: true,
    diff: true,
    changelog: false,
  });
  const [changelogs, setChangelogs] = useState<ChangelogData>({ versionA: null, versionB: null });
  const [loadingChangelogs, setLoadingChangelogs] = useState(false);

  const togglePanel = (panel: string) => {
    setExpandedPanels(prev => ({ ...prev, [panel]: !prev[panel] }));
  };

  // Fetch changelogs when versions are selected
  const fetchChangelogs = async () => {
    if (!versionA && !versionB) return;

    setLoadingChangelogs(true);
    const newChangelogs: ChangelogData = { versionA: null, versionB: null };

    try {
      if (versionA) {
        const responseA = await apiGet<{ success: boolean; changelog: string | null; filename?: string }>(
          `/api/admin/system-instructions/versions/${versionA}/changelog`
        );
        if (responseA.success) {
          newChangelogs.versionA = { changelog: responseA.changelog, filename: responseA.filename };
        }
      }

      if (versionB) {
        const responseB = await apiGet<{ success: boolean; changelog: string | null; filename?: string }>(
          `/api/admin/system-instructions/versions/${versionB}/changelog`
        );
        if (responseB.success) {
          newChangelogs.versionB = { changelog: responseB.changelog, filename: responseB.filename };
        }
      }
    } catch (err) {
      logger.error('Failed to fetch changelogs:', err);
    } finally {
      setChangelogs(newChangelogs);
      setLoadingChangelogs(false);
    }
  };

  // Fetch changelogs when comparison is run
  useEffect(() => {
    if (result) {
      fetchChangelogs();
    }
  }, [result]);

  const hasChangelogs = changelogs.versionA?.changelog || changelogs.versionB?.changelog;

  return (
    <div className="space-y-6">
      {/* Selection Panel */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-primary mb-4">Compare Versions</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Version A (Older)
            </label>
            <select
              value={versionA}
              onChange={(e) => onVersionAChange(e.target.value)}
              className="input-field w-full"
            >
              <option value="">Select version...</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_number} {v.is_active ? '(Active)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary mb-1">
              Version B (Newer)
            </label>
            <select
              value={versionB}
              onChange={(e) => onVersionBChange(e.target.value)}
              className="input-field w-full"
            >
              <option value="">Select version...</option>
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_number} {v.is_active ? '(Active)' : ''}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={onCompare}
            disabled={!versionA || !versionB || comparing}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {comparing ? (
              <span className="flex items-center justify-center gap-2">
                <LoadingSpinner size="sm" />
                Comparing...
              </span>
            ) : (
              'Generate Comparison'
            )}
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      {result && (
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-secondary">
                Comparing <span className="font-medium text-primary">{result.version_a.version_number}</span>
                {' → '}
                <span className="font-medium text-primary">{result.version_b.version_number}</span>
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-green-400">+{result.stats.additions} additions</span>
              <span className="text-red-400">-{result.stats.deletions} deletions</span>
              <span className="text-muted">({result.stats.total_changes} total changes)</span>
            </div>
          </div>
        </div>
      )}

      {/* AI Summary Panel */}
      {result && (
        <CollapsiblePanel
          title="AI Summary"
          subtitle="Natural language analysis of changes"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          }
          expanded={expandedPanels.summary}
          onToggle={() => togglePanel('summary')}
          headerAction={
            !summaryResult && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onGenerateSummary();
                }}
                disabled={generatingSummary}
                className="px-3 py-1.5 text-xs font-medium text-blue-400 hover:text-blue-300 border border-blue-500/30 rounded-lg hover:border-blue-500/50 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {generatingSummary ? (
                  <span className="flex items-center gap-1">
                    <LoadingSpinner size="sm" />
                    Generating...
                  </span>
                ) : (
                  'Generate AI Summary'
                )}
              </button>
            )
          }
        >
          {summaryResult ? (
            <div className="prose prose-invert max-w-none">
              <div className="text-secondary whitespace-pre-wrap">{summaryResult.summary}</div>
            </div>
          ) : generatingSummary ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="lg" />
              <span className="ml-3 text-secondary">Analyzing changes with Claude...</span>
            </div>
          ) : (
            <div className="text-center py-8 text-muted">
              <p>Click &quot;Generate AI Summary&quot; to get a natural language analysis of the changes.</p>
              <p className="text-sm mt-2">This uses Claude to analyze the diff and provide actionable insights.</p>
            </div>
          )}
        </CollapsiblePanel>
      )}

      {/* Diff Panel */}
      {result && (
        <CollapsiblePanel
          title="Line-by-Line Diff"
          subtitle="Technical comparison showing exact changes"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
            </svg>
          }
          expanded={expandedPanels.diff}
          onToggle={() => togglePanel('diff')}
        >
          <div className="max-h-[500px] overflow-y-auto rounded-lg bg-page border border-default p-4">
            <pre className="text-sm font-mono whitespace-pre-wrap">
              {result.diff.map((line, index) => {
                let className = 'text-secondary';
                if (line.startsWith('+') && !line.startsWith('+++')) {
                  className = 'text-green-400 bg-green-500/10';
                } else if (line.startsWith('-') && !line.startsWith('---')) {
                  className = 'text-red-400 bg-red-500/10';
                } else if (line.startsWith('@@')) {
                  className = 'text-blue-400';
                }
                return (
                  <div key={index} className={className}>
                    {line}
                  </div>
                );
              })}
            </pre>
          </div>
        </CollapsiblePanel>
      )}

      {/* Changelog Panel */}
      {result && (
        <CollapsiblePanel
          title="Version Changelogs"
          subtitle={hasChangelogs ? "Documentation files for these versions" : "No changelog files found"}
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          expanded={expandedPanels.changelog}
          onToggle={() => togglePanel('changelog')}
          badge={hasChangelogs ? undefined : 'None'}
        >
          {loadingChangelogs ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="md" />
              <span className="ml-3 text-secondary">Loading changelogs...</span>
            </div>
          ) : hasChangelogs ? (
            <div className="space-y-6">
              {changelogs.versionA?.changelog && (
                <div>
                  <h4 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
                    Version {result.version_a.version_number} Changelog
                    {changelogs.versionA.filename && (
                      <span className="ml-2 text-xs font-normal text-muted">({changelogs.versionA.filename})</span>
                    )}
                  </h4>
                  <div className="max-h-64 overflow-y-auto rounded-lg bg-page border border-default p-4">
                    <pre className="text-sm text-secondary whitespace-pre-wrap font-mono">
                      {changelogs.versionA.changelog}
                    </pre>
                  </div>
                </div>
              )}
              {changelogs.versionB?.changelog && (
                <div>
                  <h4 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
                    Version {result.version_b.version_number} Changelog
                    {changelogs.versionB.filename && (
                      <span className="ml-2 text-xs font-normal text-muted">({changelogs.versionB.filename})</span>
                    )}
                  </h4>
                  <div className="max-h-64 overflow-y-auto rounded-lg bg-page border border-default p-4">
                    <pre className="text-sm text-secondary whitespace-pre-wrap font-mono">
                      {changelogs.versionB.changelog}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-muted">
              <p>No changelog files found for these versions.</p>
              <p className="text-sm mt-2">
                Changelog files should be named like <code className="text-secondary">v1.1-changelog.md</code> or <code className="text-secondary">v1.1-update-log.md</code>
              </p>
            </div>
          )}
        </CollapsiblePanel>
      )}
    </div>
  );
}

// ============================================================================
// Collapsible Panel Component
// ============================================================================

interface CollapsiblePanelProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  headerAction?: React.ReactNode;
  badge?: string;
  children: React.ReactNode;
}

function CollapsiblePanel({
  title,
  subtitle,
  icon,
  expanded,
  onToggle,
  headerAction,
  badge,
  children,
}: CollapsiblePanelProps) {
  return (
    <div className="card overflow-hidden">
      <div className="w-full px-6 py-4 flex items-center justify-between hover:bg-hover transition-colors">
        <div
          className="flex items-center gap-3 flex-1 cursor-pointer"
          onClick={onToggle}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onToggle(); }}
        >
          {icon && <div className="text-muted">{icon}</div>}
          <div className="text-left">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-primary">{title}</h3>
              {badge && (
                <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-500/20 text-gray-400">
                  {badge}
                </span>
              )}
            </div>
            {subtitle && <p className="text-sm text-muted">{subtitle}</p>}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {headerAction}
          <button
            onClick={onToggle}
            className="p-1 cursor-pointer"
            aria-label={expanded ? 'Collapse' : 'Expand'}
          >
            <svg
              className={`w-5 h-5 text-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
      {expanded && (
        <div className="px-6 pb-6 border-t border-default pt-4">
          {children}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Modal Component
// ============================================================================

interface ViewVersionModalProps {
  version: SystemInstructionVersion;
  onClose: () => void;
  formatDate: (date: string | null) => string;
  formatFileSize: (bytes: number) => string;
}

function ViewVersionModal({ version, onClose, formatDate, formatFileSize }: ViewVersionModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-card rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-card border-b border-default px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-primary">Version {version.version_number}</h2>
            <p className="text-sm text-muted">Created {formatDate(version.created_at)}</p>
          </div>
          <button
            onClick={onClose}
            className="text-muted hover:text-primary transition-colors cursor-pointer"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {/* Metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-subtle">
              <p className="text-xs text-muted uppercase">Status</p>
              <p className="font-medium text-primary">
                {version.is_active ? 'Active' : version.status}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-subtle">
              <p className="text-xs text-muted uppercase">File Size</p>
              <p className="font-medium text-primary">{formatFileSize(version.file_size)}</p>
            </div>
            <div className="p-3 rounded-lg bg-subtle">
              <p className="text-xs text-muted uppercase">Created By</p>
              <p className="font-medium text-primary">{version.created_by_name || 'Unknown'}</p>
            </div>
            {version.activated_at && (
              <div className="p-3 rounded-lg bg-subtle">
                <p className="text-xs text-muted uppercase">Activated</p>
                <p className="font-medium text-primary">{formatDate(version.activated_at)}</p>
              </div>
            )}
          </div>

          {/* Notes */}
          {version.version_notes && (
            <div>
              <h3 className="text-sm font-medium text-muted uppercase mb-2">Version Notes</h3>
              <p className="text-secondary">{version.version_notes}</p>
            </div>
          )}

          {/* Conversation Count */}
          {version.conversation_count !== undefined && (
            <div className="p-3 rounded-lg bg-subtle">
              <p className="text-sm text-secondary">
                This version is used by <span className="font-medium text-primary">{version.conversation_count}</span> conversation(s).
              </p>
            </div>
          )}

          {/* Content */}
          <div>
            <h3 className="text-sm font-medium text-muted uppercase mb-2">Full Content</h3>
            <div className="max-h-96 overflow-y-auto rounded-lg bg-page border border-default p-4">
              <pre className="text-sm text-secondary whitespace-pre-wrap font-mono">
                {version.content}
              </pre>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-page px-6 py-4 border-t border-default">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
