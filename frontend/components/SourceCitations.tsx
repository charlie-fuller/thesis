'use client';

import { useState } from 'react';

export interface SourceDocument {
  chunk_id: string;
  document_id: string;
  document_name: string;
  relevance_score: number;
  snippet: string;
  metadata?: {
    filename?: string;
    conversation_title?: string;
    page_number?: number;
  };
}

interface SourceCitationsProps {
  sources: SourceDocument[];
  onSourceClick?: (documentId: string) => void;
}

export default function SourceCitations({ sources, onSourceClick }: SourceCitationsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());

  if (!sources || sources.length === 0) {
    return null;
  }

  const toggleSourceExpansion = (chunkId: string) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chunkId)) {
        newSet.delete(chunkId);
      } else {
        newSet.add(chunkId);
      }
      return newSet;
    });
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50';
    if (score >= 0.6) return 'text-blue-600 bg-blue-50';
    if (score >= 0.4) return 'text-amber-600 bg-amber-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getRelevanceLabel = (score: number) => {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    if (score >= 0.4) return 'Low';
    return 'Very Low';
  };

  return (
    <div className="mt-3 border-t border-default pt-3">
      {/* Collapsible header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-xs font-medium text-secondary hover:text-primary transition-colors w-full"
      >
        <span className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
          ▶
        </span>
        <span>Sources ({sources.length})</span>
      </button>

      {/* Sources list */}
      {isExpanded && (
        <div className="mt-3 space-y-2">
          {sources.map((source, index) => {
            const isSourceExpanded = expandedSources.has(source.chunk_id);

            return (
              <div
                key={source.chunk_id}
                className="border border-default rounded-lg overflow-hidden bg-card"
              >
                {/* Source header */}
                <div className="flex items-start justify-between gap-3 p-3">
                  <div className="flex-1 min-w-0">
                    {/* Document name */}
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-primary">
                        [{index + 1}]
                      </span>
                      {onSourceClick ? (
                        <button
                          onClick={() => onSourceClick(source.document_id)}
                          className="text-xs font-medium text-primary hover:text-primary-hover underline truncate"
                          title={source.document_name}
                        >
                          {source.document_name}
                        </button>
                      ) : (
                        <span
                          className="text-xs font-medium text-primary truncate"
                          title={source.document_name}
                        >
                          {source.document_name}
                        </span>
                      )}
                    </div>

                    {/* Metadata */}
                    {source.metadata?.page_number && (
                      <div className="text-xs text-muted">
                        Page {source.metadata.page_number}
                      </div>
                    )}
                  </div>

                  {/* Relevance indicator */}
                  <div className="flex items-center gap-2">
                    <div
                      className={`px-2 py-1 rounded text-xs font-medium ${getRelevanceColor(
                        source.relevance_score
                      )}`}
                      title={`Relevance score: ${(source.relevance_score * 100).toFixed(0)}%`}
                    >
                      {getRelevanceLabel(source.relevance_score)} {(source.relevance_score * 100).toFixed(0)}%
                    </div>

                    {/* Expand/collapse button */}
                    <button
                      onClick={() => toggleSourceExpansion(source.chunk_id)}
                      className="text-xs text-muted hover:text-primary transition-colors"
                      title={isSourceExpanded ? 'Hide snippet' : 'Show snippet'}
                    >
                      {isSourceExpanded ? '▲' : '▼'}
                    </button>
                  </div>
                </div>

                {/* Expandable snippet */}
                {isSourceExpanded && (
                  <div className="border-t border-default bg-hover p-3">
                    <div className="text-xs text-secondary leading-relaxed whitespace-pre-wrap">
                      {source.snippet}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
