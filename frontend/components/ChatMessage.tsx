'use client';

import { useState, memo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { logger } from '@/lib/logger';
import { apiPost } from '@/lib/api';
import SourceCitations, { SourceDocument } from './SourceCitations';
import { AgentIcon, getAgentColor } from './AgentIcon';

interface Document {
  id: string
  filename: string
  mime_type?: string
}

interface MessageMetadata {
  agent_name?: string
  agent_display_name?: string
  [key: string]: unknown
}

// State for expanded sections
interface ExpandedSection {
  content: string
  isLoading: boolean
}

interface ChatMessageProps {
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  documents?: Document[]
  sources?: SourceDocument[]
  onSourceClick?: (documentId: string) => void
  conversationId?: string
  messageId?: string
  onDigDeeper?: (messageId: string, content: string) => void
  onDigDeeperSection?: (messageId: string, content: string, sectionId: string) => Promise<string>
  isDigDeeperLoading?: boolean
  metadata?: MessageMetadata
  onSaveToKB?: (messageId: string, content: string) => void
}

// Code block component with copy button
function CodeBlock({
  language,
  value,
  conversationId,
  messageId
}: {
  language: string;
  value: string;
  conversationId?: string;
  messageId?: string;
}) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);

  const handleCopy = async () => {
    try {
      // Check if Clipboard API is available
      if (!navigator.clipboard) {
        throw new Error('Clipboard API not available');
      }

      await navigator.clipboard.writeText(value);
      setCopied(true);
      setCopyError(false);
      setTimeout(() => setCopied(false), 2000);

      // Track copy event for KPI if we have conversation context
      if (conversationId && messageId && value.length >= 50) {
        try {
          await apiPost(`/api/kpis/copy-event/${conversationId}`, {
            message_id: messageId,
            content_length: value.length
          });
          logger.debug('Copy event tracked for KPI');
        } catch (trackErr) {
          // Don't fail the copy if tracking fails
          logger.warn('Failed to track copy event:', trackErr);
        }
      }
    } catch (err) {
      logger.error('Failed to copy:', err);
      setCopyError(true);
      setTimeout(() => setCopyError(false), 2000);
    }
  };

  return (
    <div className="relative group">
      <button
        onClick={handleCopy}
        className={`absolute right-2 top-2 px-3 py-1 text-xs font-medium text-white rounded opacity-0 group-hover:opacity-100 transition-opacity ${
          copyError ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-700 hover:bg-gray-600'
        }`}
        title={copyError ? 'Copy failed' : 'Copy code'}
      >
        {copied ? 'Copied!' : copyError ? 'Failed' : 'Copy'}
      </button>
      <SyntaxHighlighter
        language={language || 'text'}
        style={oneDark}
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
          padding: '1rem',
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
}

function ChatMessage({ content, role, timestamp, documents, sources, onSourceClick, conversationId, messageId, onDigDeeper, onDigDeeperSection, isDigDeeperLoading, metadata, onSaveToKB }: ChatMessageProps) {
  // State for inline dig-deeper expanded sections
  const [expandedSections, setExpandedSections] = useState<Record<string, ExpandedSection>>({});

  // Handle inline dig-deeper link click
  const handleDigDeeperSection = useCallback(async (sectionId: string) => {
    if (!messageId || !onDigDeeperSection) return;

    // If already expanded, toggle collapse
    if (expandedSections[sectionId]?.content) {
      setExpandedSections(prev => {
        const updated = { ...prev };
        delete updated[sectionId];
        return updated;
      });
      return;
    }

    // Set loading state
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: { content: '', isLoading: true }
    }));

    try {
      const expandedContent = await onDigDeeperSection(messageId, content, sectionId);
      setExpandedSections(prev => ({
        ...prev,
        [sectionId]: { content: expandedContent, isLoading: false }
      }));
    } catch (err) {
      logger.error('Failed to expand section:', err);
      setExpandedSections(prev => {
        const updated = { ...prev };
        delete updated[sectionId];
        return updated;
      });
    }
  }, [messageId, content, onDigDeeperSection, expandedSections]);

  // Track text selection copy events for assistant messages
  const handleCopyEvent = useCallback(async () => {
    if (role !== 'assistant' || !conversationId || !messageId) return;

    const selection = window.getSelection();
    const selectedText = selection?.toString() || '';

    // Only track significant copies (50+ chars)
    if (selectedText.length >= 50) {
      try {
        await apiPost(`/api/kpis/copy-event/${conversationId}`, {
          message_id: messageId,
          content_length: selectedText.length
        });
        logger.debug('Text selection copy event tracked for KPI');
      } catch (err) {
        logger.warn('Failed to track copy event:', err);
      }
    }
  }, [role, conversationId, messageId]);

  // Format timestamp for display
  const formatTime = (isoString: string) => {
    if (!isoString) return ''
    const date = new Date(isoString)
    if (isNaN(date.getTime())) return ''
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  // Get file icon based on mime type
  const getFileIcon = (mimeType?: string) => {
    if (!mimeType) return 'DOC'
    if (mimeType.includes('pdf')) return 'PDF'
    if (mimeType.includes('word') || mimeType.includes('document')) return 'DOC'
    if (mimeType.includes('text')) return 'TXT'
    if (mimeType.includes('csv') || mimeType.includes('spreadsheet')) return 'CSV'
    return 'DOC'
  }

  return (
    <div className={`mb-4 flex ${role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={role === 'user' ? 'message-user' : 'message-assistant'}
        onCopy={handleCopyEvent}
      >
        {documents && documents.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="inline-flex items-center gap-1.5 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-md border border-blue-200"
                title={doc.mime_type}
              >
                <span>{getFileIcon(doc.mime_type)}</span>
                <span className="font-medium">{doc.filename}</span>
              </div>
            ))}
          </div>
        )}
        {/* Agent badge for assistant messages */}
        {role === 'assistant' && metadata?.agent_name && (
          <div className="mb-2">
            <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${getAgentColor(metadata.agent_name)}`}>
              <AgentIcon name={metadata.agent_name} size="sm" />
              <span>{metadata.agent_display_name || metadata.agent_name}</span>
            </div>
          </div>
        )}

        {role === 'assistant' ? (
          <div className="text-sm md:text-base prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-headings:my-3">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode; node?: unknown }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const value = String(children).replace(/\n$/, '');

                  return !inline && match ? (
                    <CodeBlock
                      language={match[1]}
                      value={value}
                      conversationId={conversationId}
                      messageId={messageId}
                    />
                  ) : (
                    <code className="bg-hover text-primary px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                      {children}
                    </code>
                  );
                },
                a({ children, href }: { children?: React.ReactNode; href?: string }) {
                  // Check if this is a dig-deeper link
                  if (href?.startsWith('dig-deeper:')) {
                    const sectionId = href.replace('dig-deeper:', '');
                    const section = expandedSections[sectionId];
                    const isLoading = section?.isLoading;
                    const isExpanded = section?.content;

                    return (
                      <span className="inline-block">
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            handleDigDeeperSection(sectionId);
                          }}
                          disabled={isLoading}
                          className="inline-flex items-center gap-1 text-teal-600 hover:text-teal-700 underline text-sm font-medium disabled:opacity-50 disabled:cursor-wait"
                          title={isExpanded ? 'Click to collapse' : 'Click to expand'}
                        >
                          {isLoading ? (
                            <>
                              <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              <span>Loading...</span>
                            </>
                          ) : (
                            <>
                              {children}
                              <svg
                                className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </>
                          )}
                        </button>
                        {/* Expanded content inline */}
                        {isExpanded && (
                          <div className="mt-2 mb-3 pl-3 border-l-2 border-teal-300 bg-teal-50/50 rounded-r-md py-2 pr-2">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                // Simpler rendering for expanded content - no nested dig-deeper
                                a({ children: linkChildren, href: linkHref }: { children?: React.ReactNode; href?: string }) {
                                  if (linkHref?.startsWith('dig-deeper:')) {
                                    // Render nested dig-deeper as plain text for now
                                    return <span className="text-teal-600 font-medium">{linkChildren}</span>;
                                  }
                                  return (
                                    <a href={linkHref} target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:text-teal-700 underline">
                                      {linkChildren}
                                    </a>
                                  );
                                },
                              }}
                            >
                              {section.content}
                            </ReactMarkdown>
                          </div>
                        )}
                      </span>
                    );
                  }

                  // Regular external link
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-teal-600 hover:text-teal-700 underline"
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="text-sm md:text-base whitespace-pre-wrap break-words">
            {content}
          </div>
        )}

        {/* Source citations for assistant messages */}
        {role === 'assistant' && sources && sources.length > 0 && (
          <SourceCitations sources={sources} onSourceClick={onSourceClick} />
        )}

        {/* Action buttons for assistant messages */}
        {role === 'assistant' && content && content.length > 100 && messageId && (
          <div className="mt-3 pt-2 border-t border-default flex items-center gap-2">
            {onDigDeeper && (
              <button
                onClick={() => onDigDeeper(messageId, content)}
                disabled={isDigDeeperLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted hover:text-primary bg-hover hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Get more detail on this response"
              >
                {isDigDeeperLoading ? (
                  <>
                    <svg className="animate-spin h-3.5 w-3.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Elaborating...</span>
                  </>
                ) : (
                  <>
                    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                    <span>Dig Deeper</span>
                  </>
                )}
              </button>
            )}
            {onSaveToKB && (
              <button
                onClick={() => onSaveToKB(messageId, content)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted hover:text-primary bg-hover hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors"
                title="Save this response to your knowledge base"
              >
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                <span>Save to KB</span>
              </button>
            )}
          </div>
        )}

        <div className="message-timestamp" title={timestamp}>
          {formatTime(timestamp)}
        </div>
      </div>
    </div>
  )
}

export default memo(ChatMessage);
