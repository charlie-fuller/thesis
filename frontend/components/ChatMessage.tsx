'use client';

import { useState, memo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { logger } from '@/lib/logger';
import { apiPost } from '@/lib/api';
import SourceCitations, { SourceDocument } from './SourceCitations';

interface Document {
  id: string
  filename: string
  mime_type?: string
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

function ChatMessage({ content, role, timestamp, documents, sources, onSourceClick, conversationId, messageId }: ChatMessageProps) {
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
                    <code className="bg-gray-200 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                      {children}
                    </code>
                  );
                },
                a({ children, href }: { children?: React.ReactNode; href?: string }) {
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

        <div className="message-timestamp" title={timestamp}>
          {formatTime(timestamp)}
        </div>
      </div>
    </div>
  )
}

export default memo(ChatMessage);
