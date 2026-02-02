'use client';

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { API_BASE_URL } from '@/lib/config';
import { supabase } from '@/lib/supabase';

const HELP_PANEL_STORAGE_KEY = 'thesis-help-panel-open';

export interface HelpMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    title: string;
    section: string;
    file_path: string;
    similarity: number;
  }>;
  timestamp: string;
  feedback?: number; // 1 for thumbs up, -1 for thumbs down, null for no feedback
}

export interface HelpConversation {
  id: string;
  title: string;
  messages: HelpMessage[];
  created_at: string;
  updated_at: string;
}

interface HelpChatContextType {
  isOpen: boolean;
  isMinimized: boolean;
  currentConversation: HelpConversation | null;
  conversations: HelpConversation[];
  loading: boolean;
  setIsOpen: (open: boolean) => void;
  setIsMinimized: (minimized: boolean) => void;
  toggleOpen: () => void;
  toggleMinimize: () => void;
  startNewConversation: () => void;
  loadConversation: (id: string) => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  loadConversations: () => Promise<void>;
  submitFeedback: (messageId: string, feedback: number) => Promise<void>;
}

const HelpChatContext = createContext<HelpChatContextType | undefined>(undefined);

export function HelpChatProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpenState] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [stateLoaded, setStateLoaded] = useState(false);

  // Load saved state from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(HELP_PANEL_STORAGE_KEY);
    if (saved !== null) {
      setIsOpenState(saved === 'true');
    }
    setStateLoaded(true);
  }, []);

  // Persist to localStorage when isOpen changes (after initial load)
  useEffect(() => {
    if (stateLoaded) {
      localStorage.setItem(HELP_PANEL_STORAGE_KEY, String(isOpen));
    }
  }, [isOpen, stateLoaded]);

  // Wrapper for setIsOpen that updates state
  const setIsOpen = useCallback((open: boolean) => {
    setIsOpenState(open);
  }, []);
  const [currentConversation, setCurrentConversation] = useState<HelpConversation | null>(null);
  const [conversations, setConversations] = useState<HelpConversation[]>([]);
  const [loading, setLoading] = useState(false);

  // Helper to get auth headers
  const getAuthHeaders = useCallback(async () => {
    const { data: { session } } = await supabase.auth.getSession();
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }
    return headers;
  }, []);

  const toggleOpen = useCallback(() => {
    setIsOpenState((prev) => !prev);
    if (!isOpen) {
      setIsMinimized(false);
    }
  }, [isOpen]);

  const toggleMinimize = useCallback(() => {
    setIsMinimized((prev) => !prev);
  }, []);

  const startNewConversation = useCallback(() => {
    setCurrentConversation({
      id: 'new',
      title: 'New Help Chat',
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }, []);

  const loadConversations = useCallback(async () => {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/help/conversations`, { headers });
      if (!response.ok) throw new Error('Failed to load conversations');
      const data = await response.json();
      setConversations(data);
    } catch {
      // Silently handle errors loading conversations
    }
  }, [getAuthHeaders]);

  const loadConversation = useCallback(async (id: string) => {
    setLoading(true);
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/help/conversations/${id}`, { headers });
      if (!response.ok) throw new Error('Failed to load conversation');
      const data = await response.json();
      setCurrentConversation(data);
    } catch {
      // Silently handle errors loading conversation
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    // Add user message optimistically
    const userMessage: HelpMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    const updatedMessages = [...(currentConversation?.messages || []), userMessage];

    setCurrentConversation((prev) => ({
      id: prev?.id || 'new',
      title: prev?.title || message.slice(0, 50),
      messages: updatedMessages,
      created_at: prev?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));

    setLoading(true);

    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/help/ask`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          conversation_id: currentConversation?.id !== 'new' ? currentConversation?.id : undefined,
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();

      // Add assistant message
      const assistantMessage: HelpMessage = {
        id: data.message_id,
        role: 'assistant',
        content: data.response,
        sources: data.sources,
        timestamp: new Date().toISOString(),
      };

      setCurrentConversation((prev) => ({
        id: data.conversation_id,
        title: prev?.title || message.slice(0, 50),
        messages: [...updatedMessages, assistantMessage],
        created_at: prev?.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));

      // Reload conversations list to update sidebar
      loadConversations();
    } catch {
      // Remove optimistic user message on error
      setCurrentConversation((prev) => ({
        ...prev!,
        messages: prev?.messages.slice(0, -1) || [],
      }));
    } finally {
      setLoading(false);
    }
  }, [currentConversation, loadConversations, getAuthHeaders]);

  const deleteConversation = useCallback(async (id: string) => {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/help/conversations/${id}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) throw new Error('Failed to delete conversation');

      // Remove from list
      setConversations((prev) => prev.filter((conv) => conv.id !== id));

      // Clear current if deleted
      if (currentConversation?.id === id) {
        startNewConversation();
      }
    } catch {
      // Silently handle deletion errors
    }
  }, [currentConversation, startNewConversation, getAuthHeaders]);

  const submitFeedback = useCallback(async (messageId: string, feedback: number) => {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/help/feedback/${messageId}?feedback=${feedback}`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) throw new Error('Failed to submit feedback');

      // Update local state to reflect feedback
      setCurrentConversation((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === messageId ? { ...msg, feedback } : msg
          ),
        };
      });
    } catch {
      // Silently handle feedback errors
    }
  }, [getAuthHeaders]);

  const value: HelpChatContextType = {
    isOpen,
    isMinimized,
    currentConversation,
    conversations,
    loading,
    setIsOpen,
    setIsMinimized,
    toggleOpen,
    toggleMinimize,
    startNewConversation,
    loadConversation,
    sendMessage,
    deleteConversation,
    loadConversations,
    submitFeedback,
  };

  return <HelpChatContext.Provider value={value}>{children}</HelpChatContext.Provider>;
}

export function useHelpChat() {
  const context = useContext(HelpChatContext);
  if (context === undefined) {
    throw new Error('useHelpChat must be used within a HelpChatProvider');
  }
  return context;
}
