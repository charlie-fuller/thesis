/**
 * Common API Response Types
 *
 * These type definitions provide type safety for API responses throughout the application.
 * Use these instead of `any` types when handling API calls.
 */

// ============================================================================
// Generic API Response Wrapper
// ============================================================================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  limit: number;
  offset: number;
  hasMore?: boolean;
}

// ============================================================================
// Document Types
// ============================================================================

export interface Document {
  id: string;
  filename: string;
  file_type: string | null;
  file_size: number;
  client_id: string;
  user_id?: string;
  uploaded_at: string;
  uploaded_by?: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_error?: string | null;
  chunk_count: number;
  access_count: number;
  storage_url?: string;
  source_platform?: 'upload' | 'obsidian';
  external_url?: string;
}

export interface DocumentWithRelations extends Document {
  clients?: { name: string };
  users?: { email: string };
}

export interface DocumentsResponse {
  success: boolean;
  documents: Document[];
}

// ============================================================================
// User Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  name?: string | null;
  role: 'admin' | 'user';
  avatar_url?: string | null;
  client_id: string;
  created_at: string;
  storage_quota: number;
  storage_used: number;
}

// UserProfile is an alias for User - can be extended with additional fields if needed
export type UserProfile = User;

// ============================================================================
// Conversation Types
// ============================================================================

export interface Message {
  id?: string;
  conversation_id?: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  created_at?: string;
  imageLoading?: boolean;  // True while image is being generated
  imageId?: string;         // ID of the generated image
}

export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  client_id: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  in_knowledge_base?: boolean;
  added_to_kb_at?: string | null;
  archived?: boolean;
  archived_at?: string | null;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

export interface ConversationsResponse {
  success: boolean;
  conversations: Conversation[];
}

// ============================================================================
// Quick Prompts Types
// ============================================================================

export interface QuickPrompt {
  id: string;
  prompt_text: string;
  function_name?: string;
  usage_count: number;
  active: boolean;
  display_order?: number;
  created_at?: string;
}

export interface QuickPromptsResponse {
  success: boolean;
  prompts: QuickPrompt[];
}

// ============================================================================
// Storage Types
// ============================================================================

export interface StorageInfo {
  quota: number;
  used: number;
  remaining: number;
  percentage: number;
}

export interface StorageResponse {
  success: boolean;
  storage_quota: number;
  storage_used: number;
}

// ============================================================================
// Error Types
// ============================================================================

export interface ApiError {
  message: string;
  code?: string;
  statusCode?: number;
  details?: Record<string, unknown>;
}

// ============================================================================
// Streaming Response Types
// ============================================================================

export interface StreamingTokenData {
  type: 'token';
  token: string;
}

export interface StreamingChunk {
  text: string;
  document_id?: string;
  score?: number;
}

export interface StreamingContextData {
  type: 'context';
  count: number;
  chunks?: StreamingChunk[];
}

export interface StreamingDoneData {
  type: 'done';
  tokens?: number;
  cost?: number;
}

export interface StreamingErrorData {
  type: 'error';
  error: string;
}

export type StreamingData =
  | StreamingTokenData
  | StreamingContextData
  | StreamingDoneData
  | StreamingErrorData;

// ============================================================================
// Analytics & KPI Types
// ============================================================================

export interface KPI {
  ideation_velocity: number;
  correction_loop_rate: number;
  output_usefulness: number;
  calculated_at: string;
}

export interface UsageStats {
  total_conversations: number;
  total_messages: number;
  total_documents: number;
  active_users: number;
}
