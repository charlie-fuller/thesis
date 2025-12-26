'use client';

import { useState, useEffect } from 'react';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';

interface Document {
  id: string;
  filename: string;
  mime_type?: string;
  file_size?: number;
  uploaded_at?: string;
}

interface DocumentScopeSelectorProps {
  selectedDocumentIds: string[];
  onSelectionChange: (documentIds: string[]) => void;
  className?: string;
}

export default function DocumentScopeSelector({
  selectedDocumentIds,
  onSelectionChange,
  className = ''
}: DocumentScopeSelectorProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchMode, setSearchMode] = useState<'all' | 'selected'>('all');

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError(null);
      const response = await apiGet<{ documents: Document[] }>('/api/documents/users/me');
      setDocuments(response.documents || []);
    } catch (err) {
      logger.error('Failed to load documents:', err);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  }

  const handleToggleDocument = (documentId: string) => {
    const newSelection = selectedDocumentIds.includes(documentId)
      ? selectedDocumentIds.filter(id => id !== documentId)
      : [...selectedDocumentIds, documentId];

    onSelectionChange(newSelection);
  };

  const handleSelectAll = () => {
    onSelectionChange(documents.map(doc => doc.id));
  };

  const handleDeselectAll = () => {
    onSelectionChange([]);
  };

  const handleSearchModeChange = (mode: 'all' | 'selected') => {
    setSearchMode(mode);
    if (mode === 'all') {
      onSelectionChange([]);
    }
  };

  const getFileIcon = (mimeType?: string) => {
    if (!mimeType) return 'DOC';
    if (mimeType.includes('pdf')) return 'PDF';
    if (mimeType.includes('word') || mimeType.includes('document')) return 'DOC';
    if (mimeType.includes('text')) return 'TXT';
    if (mimeType.includes('csv') || mimeType.includes('spreadsheet')) return 'CSV';
    return 'DOC';
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className={`border border-default rounded-lg bg-card ${className}`}>
      {/* Header with toggle */}
      <div className="p-3 border-b border-default">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center justify-between w-full text-sm font-medium text-primary hover:text-primary-hover transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
              ▶
            </span>
            <span>Document Search Scope</span>
          </div>
          <span className="text-xs text-muted">
            {searchMode === 'all'
              ? 'Searching all documents'
              : `${selectedDocumentIds.length} selected`}
          </span>
        </button>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="p-3">
          {/* Search mode selector */}
          <div className="flex gap-2 mb-3">
            <button
              onClick={() => handleSearchModeChange('all')}
              className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                searchMode === 'all'
                  ? 'bg-primary text-on-primary'
                  : 'bg-hover text-secondary border border-default hover:bg-hover'
              }`}
            >
              All Documents
            </button>
            <button
              onClick={() => handleSearchModeChange('selected')}
              className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                searchMode === 'selected'
                  ? 'bg-primary text-on-primary'
                  : 'bg-hover text-secondary border border-default hover:bg-hover'
              }`}
            >
              Selected Only
            </button>
          </div>

          {/* Document list (only show when 'selected' mode) */}
          {searchMode === 'selected' && (
            <>
              {loading ? (
                <div className="text-xs text-muted text-center py-4">Loading documents...</div>
              ) : error ? (
                <div className="text-xs text-error text-center py-4">{error}</div>
              ) : documents.length === 0 ? (
                <div className="text-xs text-muted text-center py-4">
                  No documents uploaded yet
                </div>
              ) : (
                <>
                  {/* Select all/none buttons */}
                  <div className="flex gap-2 mb-2">
                    <button
                      onClick={handleSelectAll}
                      className="text-xs text-primary hover:text-primary-hover underline"
                    >
                      Select All
                    </button>
                    <span className="text-xs text-muted">•</span>
                    <button
                      onClick={handleDeselectAll}
                      className="text-xs text-primary hover:text-primary-hover underline"
                    >
                      Deselect All
                    </button>
                  </div>

                  {/* Document checkboxes */}
                  <div className="space-y-1 max-h-60 overflow-y-auto">
                    {documents.map(doc => (
                      <label
                        key={doc.id}
                        className="flex items-start gap-2 p-2 rounded hover:bg-hover cursor-pointer transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDocumentIds.includes(doc.id)}
                          onChange={() => handleToggleDocument(doc.id)}
                          className="mt-0.5 focus-ring"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="text-sm">{getFileIcon(doc.mime_type)}</span>
                            <span className="text-xs font-medium text-primary truncate">
                              {doc.filename}
                            </span>
                          </div>
                          {doc.file_size && (
                            <div className="text-xs text-muted">
                              {formatFileSize(doc.file_size)}
                            </div>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </>
              )}
            </>
          )}

          {/* Info text */}
          <div className="mt-3 text-xs text-muted">
            {searchMode === 'all'
              ? 'Thesis will search through all your uploaded documents when answering questions.'
              : selectedDocumentIds.length === 0
              ? 'Select documents to search. With no selection, all documents will be searched.'
              : `Thesis will only search in the ${selectedDocumentIds.length} selected document${
                  selectedDocumentIds.length === 1 ? '' : 's'
                }.`}
          </div>
        </div>
      )}
    </div>
  );
}
