'use client';

import { useState, useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { useHelpChat } from '@/contexts/HelpChatContext';
import { useAuth } from '@/contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import MarkdownText from './MarkdownText';

const CONTEXTUAL_QUESTIONS: Record<string, string[]> = {
  '/disco': [
    'What is DISCo and how does the workflow work?',
    'How do I create a new initiative?',
    'What does each DISCo agent do?',
  ],
  '/kb': [
    'How do I upload documents to the Knowledge Base?',
    'How does document auto-classification work?',
    'What file types are supported?',
  ],
  '/chat': [
    'How do I mention a specific agent in chat?',
    'What is Auto mode vs selecting an agent?',
    'Can agents access my Knowledge Base documents?',
  ],
  '/tasks': [
    'How do I create a new task?',
    'How do I change task priority or status?',
    'Can tasks be auto-extracted from documents?',
  ],
  '/projects': [
    'How does project scoring work?',
    'What are the project tiers?',
    'How do I change a project status?',
  ],
  '/': [
    'What can I do with Thesis?',
    'How do I upload my reference documents?',
    'How do I organize my work into projects?',
    'What agents are available?',
    'How do meeting rooms work?',
  ],
};

function getContextualQuestions(pathname: string, isAdmin: boolean): string[] {
  if (CONTEXTUAL_QUESTIONS[pathname]) return CONTEXTUAL_QUESTIONS[pathname];
  for (const route of Object.keys(CONTEXTUAL_QUESTIONS)) {
    if (pathname.startsWith(route + '/')) return CONTEXTUAL_QUESTIONS[route];
  }
  if (isAdmin) {
    return ['How do I add a new user?', 'How do I customize the theme?', 'How do I export conversation history?'];
  }
  return ['What can I do with Thesis?', 'How do I upload my reference documents?', 'How do I organize my work into projects?'];
}

export default function HelpChatFullPage() {
  const { isAdmin } = useAuth();
  const pathname = usePathname();
  const contextualQuestions = getContextualQuestions(pathname, isAdmin);
  const {
    currentConversation,
    conversations,
    loading,
    startNewConversation,
    loadConversation,
    sendMessage,
    deleteConversation,
    loadConversations,
    submitFeedback,
  } = useHelpChat();

  const [input, setInput] = useState('');
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversations.length === 0) loadConversations();
  }, [conversations.length, loadConversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentConversation?.messages]);

  useEffect(() => {
    if (!currentConversation) startNewConversation();
  }, [currentConversation, startNewConversation]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const message = input;
    setInput('');
    await sendMessage(message);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleSourceExpansion = (messageId: string) => {
    setExpandedSources((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) newSet.delete(messageId);
      else newSet.add(messageId);
      return newSet;
    });
  };

  return (
    <div className="flex h-full" style={{ minHeight: 0 }}>
      {/* Conversation sidebar */}
      <div className="w-64 border-r border-default flex flex-col bg-subtle flex-shrink-0">
        <div className="p-3 border-b border-default flex items-center justify-between">
          <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Conversations</span>
          <button
            onClick={startNewConversation}
            className="p-1.5 hover:bg-hover rounded transition-colors"
            title="New conversation"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-muted" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="text-sm text-muted italic p-2">No conversations yet</div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`flex items-center justify-between p-2 rounded cursor-pointer group transition-colors ${
                  currentConversation?.id === conv.id ? 'bg-hover' : 'hover:bg-hover'
                }`}
                onClick={() => loadConversation(conv.id)}
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>{conv.title}</div>
                  <div className="text-xs text-muted">{new Date(conv.created_at).toLocaleDateString()}</div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-error hover:text-white rounded transition-all flex-shrink-0"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4" aria-live="polite" aria-label="Help chat messages">
          {!currentConversation || currentConversation.messages.length === 0 ? (
            <div className="max-w-2xl mx-auto py-12">
              <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
                Ask anything about Thesis
              </h2>
              <p className="text-muted mb-6">
                Get instant answers powered by our documentation. Try one of these questions:
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {contextualQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInput(question)}
                    className="text-left px-4 py-3 bg-subtle hover:bg-hover rounded-lg transition-colors border border-default"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    <span className="text-muted mr-2">?</span>{question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {currentConversation.messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[75%] rounded-lg p-4 ${
                      message.role === 'user' ? 'bg-primary text-white' : 'bg-subtle border border-default'
                    }`}
                    style={
                      message.role === 'user'
                        ? { backgroundColor: 'var(--color-primary)', color: 'white' }
                        : { color: 'var(--color-text-primary)' }
                    }
                  >
                    {message.role === 'user' ? (
                      <div className="whitespace-pre-wrap" style={{ color: 'white' }}>{message.content}</div>
                    ) : (
                      <MarkdownText content={message.content} />
                    )}

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-default">
                        <button
                          onClick={() => toggleSourceExpansion(message.id)}
                          className="flex items-center gap-1 text-xs font-medium text-muted hover:text-base transition-colors"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className={`h-4 w-4 transition-transform ${expandedSources.has(message.id) ? 'rotate-90' : ''}`}
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                          <span>{message.sources.length} source{message.sources.length !== 1 ? 's' : ''}</span>
                        </button>
                        {expandedSources.has(message.id) && (
                          <div className="mt-2 space-y-1.5">
                            {message.sources.map((source, idx) => (
                              <div key={idx} className="text-xs p-2 bg-page rounded border border-default">
                                <div className="font-medium flex items-center justify-between">
                                  <span>{source.title}</span>
                                  <span className="text-muted">{Math.round(source.similarity * 100)}%</span>
                                </div>
                                <div className="text-muted mt-0.5">{source.section}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Feedback */}
                    {message.role === 'assistant' && (
                      <div className="mt-2 pt-2 border-t border-default flex items-center gap-2">
                        <button
                          onClick={() => submitFeedback(message.id, 1)}
                          disabled={message.feedback !== undefined}
                          className={`p-1 rounded transition-colors ${message.feedback === 1 ? 'text-success' : 'text-muted hover:text-success'} disabled:opacity-50`}
                          title="Helpful"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill={message.feedback === 1 ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                          </svg>
                        </button>
                        <button
                          onClick={() => submitFeedback(message.id, -1)}
                          disabled={message.feedback !== undefined}
                          className={`p-1 rounded transition-colors ${message.feedback === -1 ? 'text-error' : 'text-muted hover:text-error'} disabled:opacity-50`}
                          title="Not helpful"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill={message.feedback === -1 ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {loading && (
            <div className="max-w-3xl mx-auto flex justify-start">
              <div className="bg-subtle border border-default rounded-lg p-4">
                <LoadingSpinner size="sm" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-default">
          <div className="max-w-3xl mx-auto flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question..."
              className="flex-1 p-3 border border-default rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary bg-page"
              style={{ minHeight: '44px', maxHeight: '120px', color: 'var(--color-text-primary)' }}
              rows={1}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-4 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
              style={{ backgroundColor: 'var(--color-primary)', color: 'white' }}
            >
              {loading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                </svg>
              )}
            </button>
          </div>
          <div className="max-w-3xl mx-auto text-xs text-muted mt-2">Press Enter to send, Shift+Enter for new line</div>
        </div>
      </div>
    </div>
  );
}
