/**
 * API utilities for making authenticated requests
 */

import { supabase } from './supabase';
import { API_BASE_URL } from './config';
import { logger } from './logger';

const API_BASE = API_BASE_URL;

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
  timeout?: number; // Timeout in milliseconds
}

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Make an authenticated API request
 * Automatically adds the JWT token from Supabase auth
 */
export async function authenticatedFetch(
  endpoint: string,
  options: RequestOptions = {}
): Promise<Response> {
  // Get current session
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Check if we have a valid session
  if (!session?.access_token) {
    logger.error('No valid session found. User may need to log in.');
    throw new Error('Authentication required. Please log in and try again.');
  }

  // Build headers
  const headers: Record<string, string> = {
    ...options.headers,
  };

  // Only add Content-Type if body is not FormData (browser will set it automatically for FormData)
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Add authorization header
  headers['Authorization'] = `Bearer ${session.access_token}`;

  // Make the request
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  // Add timeout to prevent hanging requests (default 30s, configurable via options.timeout)
  const controller = new AbortController();
  const timeoutMs = options.timeout || 30000;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout - please try again');
    }
    throw error;
  }
}

/**
 * Helper to handle API response and errors
 */
async function handleResponse<T = unknown>(response: Response): Promise<T> {
  // Clone response first so we can read body twice if needed
  const responseClone = response.clone();

  if (!response.ok) {
    let errorData: Record<string, unknown> = {};
    try {
      errorData = await response.json();
    } catch {
      // Response body is not JSON, use clone to read as text
      try {
        errorData = { message: await responseClone.text() };
      } catch {
        errorData = { message: `Request failed with status ${response.status}` };
      }
    }

    throw new APIError(
      (errorData.detail as string) || (errorData.message as string) || `Request failed with status ${response.status}`,
      response.status,
      errorData
    );
  }

  // Try to parse JSON, return empty object if no content
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json();
  }

  return {} as T;
}

/**
 * Make a GET request with authentication
 * @throws {APIError} If the request fails
 */
export async function apiGet<T = unknown>(endpoint: string): Promise<T> {
  const response = await authenticatedFetch(endpoint, { method: 'GET' });
  return handleResponse<T>(response);
}

/**
 * Make a POST request with authentication
 * @param options.timeout - Optional timeout in milliseconds (default 30s)
 * @throws {APIError} If the request fails
 */
export async function apiPost<T = unknown, D extends object = Record<string, unknown>>(
  endpoint: string,
  data?: D,
  options?: { timeout?: number }
): Promise<T> {
  const response = await authenticatedFetch(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
    timeout: options?.timeout,
  });
  return handleResponse<T>(response);
}

/**
 * Make a PUT request with authentication
 * @throws {APIError} If the request fails
 */
export async function apiPut<T = unknown, D extends object = Record<string, unknown>>(endpoint: string, data?: D): Promise<T> {
  const response = await authenticatedFetch(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
  return handleResponse<T>(response);
}

/**
 * Make a PATCH request with authentication
 * @throws {APIError} If the request fails
 */
export async function apiPatch<T = unknown, D extends object = Record<string, unknown>>(endpoint: string, data?: D): Promise<T> {
  const response = await authenticatedFetch(endpoint, {
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  });
  return handleResponse<T>(response);
}

/**
 * Make a DELETE request with authentication
 * @throws {APIError} If the request fails
 */
export async function apiDelete<T = unknown, D extends object = Record<string, unknown>>(endpoint: string, data?: D): Promise<T> {
  const response = await authenticatedFetch(endpoint, {
    method: 'DELETE',
    body: data ? JSON.stringify(data) : undefined,
  });
  return handleResponse<T>(response);
}

// ============================================================================
// Image Generation API Methods
// ============================================================================

export interface ImageGenerationRequest {
  prompt: string;
  model?: string;
}

export interface ImageGenerationResponse {
  image_data: string; // Base64-encoded image
  mime_type: string;
  prompt: string;
  model: string;
  success: boolean;
}

export interface BatchImageGenerationRequest {
  prompts: string[];
  model?: string;
}

export interface BatchImageGenerationResponse {
  results: ImageGenerationResponse[];
  total: number;
  successful: number;
}

export interface ImageModel {
  id: string;
  name: string;
  description: string;
  default: boolean;
}

/**
 * Generate a single image from a text prompt
 * @throws {APIError} If the request fails
 */
export async function generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
  logger.info('Generating image with Nano Banana', { prompt: request.prompt.substring(0, 50) });

  // Use longer timeout for image generation (60s)
  return apiPost<ImageGenerationResponse, ImageGenerationRequest>(
    '/api/images/generate',
    request,
    { timeout: 60000 }
  );
}

/**
 * Generate multiple images from a list of prompts
 * @throws {APIError} If the request fails
 */
export async function generateImageBatch(request: BatchImageGenerationRequest): Promise<BatchImageGenerationResponse> {
  logger.info('Generating batch of images', { count: request.prompts.length });

  // Use longer timeout for batch generation (120s)
  return apiPost<BatchImageGenerationResponse, BatchImageGenerationRequest>(
    '/api/images/generate-batch',
    request,
    { timeout: 120000 }
  );
}

/**
 * Get list of available image generation models and aspect ratios
 * @throws {APIError} If the request fails
 */
export async function getImageModels(): Promise<{
  models: ImageModel[];
  aspect_ratios: Array<{
    ratio: string;
    width: number;
    height: number;
    description: string;
  }>;
  default_model: string;
}> {
  return apiGet('/api/images/models');
}

// ============================================================================
// Conversation Image API Methods
// ============================================================================

export interface ConversationImageRequest {
  conversation_id: string;
  message_id?: string;
  prompt: string;
  aspect_ratio?: string;
  model?: string;
}

export interface ConversationImage {
  id: string;
  storage_url: string;
  prompt: string;
  aspect_ratio: string;
  model: string;
  mime_type: string;
  file_size: number;
  generated_at: string;
  conversation_id: string;
  message_id?: string;
}

export interface ConversationImageResponse extends ConversationImage {
  success: boolean;
}

export interface ConversationImagesResponse {
  conversation_id: string;
  images: ConversationImage[];
  total: number;
}

/**
 * Generate an image within a conversation context
 * @throws {APIError} If the request fails
 */
export async function generateConversationImage(
  request: ConversationImageRequest
): Promise<ConversationImageResponse> {
  logger.info('Generating conversation image', {
    conversationId: request.conversation_id,
    prompt: request.prompt.substring(0, 50)
  });

  // Use longer timeout for image generation (60s)
  return apiPost<ConversationImageResponse, ConversationImageRequest>(
    '/api/images/generate-in-conversation',
    request,
    { timeout: 60000 }
  );
}

/**
 * Get all images for a conversation
 * @throws {APIError} If the request fails
 */
export async function getConversationImages(
  conversationId: string
): Promise<ConversationImagesResponse> {
  return apiGet<ConversationImagesResponse>(
    `/api/images/conversations/${conversationId}`
  );
}

/**
 * Delete a conversation image
 * @throws {APIError} If the request fails
 */
export async function deleteConversationImage(imageId: string): Promise<{ success: boolean; message: string }> {
  logger.info('Deleting conversation image', { imageId });
  return apiDelete<{ success: boolean; message: string }>(`/api/images/${imageId}`);
}

// ============================================================================
// Quick Prompts API Methods
// ============================================================================

export interface QuickPrompt {
  id: string;
  user_id: string;
  client_id?: string;
  prompt_text: string;
  function_name?: string;
  system_generated: boolean;
  editable: boolean;
  active: boolean;
  display_order?: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface ContextualPromptsRequest {
  conversation_text: string;
  addie_phase?: string;
  limit?: number;
}

export interface ContextualPromptsResponse {
  success: boolean;
  count: number;
  prompts: QuickPrompt[];
}

/**
 * Get contextually relevant quick prompts based on conversation content
 * @throws {APIError} If the request fails
 */
export async function getContextualPrompts(
  request: ContextualPromptsRequest
): Promise<ContextualPromptsResponse> {
  return apiPost<ContextualPromptsResponse, ContextualPromptsRequest>(
    '/api/quick-prompts/contextual',
    request
  );
}

/**
 * Track usage of a quick prompt
 * @throws {APIError} If the request fails
 */
export async function trackPromptUsage(promptId: string): Promise<{ success: boolean; usage_count: number }> {
  return apiPost<{ success: boolean; usage_count: number }>(`/api/quick-prompts/${promptId}/use`);
}

// ============================================================================
// Phase Guidance API Methods
// ============================================================================

export interface PhaseGuidanceRequest {
  conversation_id: string;
  include_prompts?: boolean;
}

export interface PhaseGuidanceResponse {
  success: boolean;
  phase: string;
  missing_required: string[];
  missing_recommended: string[];
  completeness: number;
  suggestion: string;
  suggested_prompts: string[];
  error?: string;
}

/**
 * Get proactive phase guidance for a conversation
 * Analyzes the conversation and returns suggestions for addressing gaps
 */
export async function getPhaseGuidance(request: PhaseGuidanceRequest): Promise<PhaseGuidanceResponse> {
  return apiPost<PhaseGuidanceResponse, PhaseGuidanceRequest>('/api/chat/phase-guidance', request);
}

// ============================================================================
// Project API Methods
// ============================================================================

export interface Project {
  id: string;
  user_id: string;
  client_id: string;
  title: string;
  description?: string;
  current_phase: string;
  status: string;
  created_at: string;
  updated_at: string;
  conversations?: ProjectConversation[];
  conversation_count?: number;
}

export interface ProjectConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at?: string;
  addie_phase?: string;
}

export interface ProjectCreateRequest {
  title: string;
  description?: string;
  current_phase?: string;
  client_id?: string;
}

export interface ProjectUpdateRequest {
  title?: string;
  description?: string;
  current_phase?: string;
  status?: string;
}

export interface ProjectsResponse {
  success: boolean;
  projects: Project[];
}

export interface ProjectResponse {
  success: boolean;
  project: Project;
}

/**
 * Create a new project
 */
export async function createProject(request: ProjectCreateRequest): Promise<ProjectResponse> {
  return apiPost<ProjectResponse, ProjectCreateRequest>('/api/projects/create', request);
}

/**
 * Get all projects for the current user
 */
export async function getProjects(status?: string): Promise<ProjectsResponse> {
  const endpoint = status ? `/api/projects?status=${status}` : '/api/projects';
  return apiGet<ProjectsResponse>(endpoint);
}

/**
 * Get a specific project with its conversations
 */
export async function getProject(projectId: string): Promise<ProjectResponse> {
  return apiGet<ProjectResponse>(`/api/projects/${projectId}`);
}

/**
 * Update a project
 */
export async function updateProject(projectId: string, request: ProjectUpdateRequest): Promise<ProjectResponse> {
  return apiPatch<ProjectResponse, ProjectUpdateRequest>(`/api/projects/${projectId}`, request);
}

/**
 * Delete a project
 */
export async function deleteProject(projectId: string): Promise<{ success: boolean; message: string }> {
  return apiDelete<{ success: boolean; message: string }>(`/api/projects/${projectId}`);
}

/**
 * Add a conversation to a project
 */
export async function addConversationToProject(
  projectId: string,
  conversationId: string
): Promise<{ success: boolean; message: string }> {
  return apiPost<{ success: boolean; message: string }, { conversation_id: string }>(
    `/api/projects/${projectId}/conversations`,
    { conversation_id: conversationId }
  );
}

/**
 * Remove a conversation from a project
 */
export async function removeConversationFromProject(
  projectId: string,
  conversationId: string
): Promise<{ success: boolean; message: string }> {
  return apiDelete<{ success: boolean; message: string }>(
    `/api/projects/${projectId}/conversations/${conversationId}`
  );
}

/**
 * Get all conversations in a project
 */
export async function getProjectConversations(projectId: string): Promise<{
  success: boolean;
  conversations: ProjectConversation[];
}> {
  return apiGet(`/api/projects/${projectId}/conversations`);
}

// ============================================================================
// Learning Outcomes API Methods
// ============================================================================

export interface LearningOutcome {
  id: string;
  project_id: string;
  user_id: string;
  title: string;
  description?: string;
  metric_type: string;
  baseline_value?: number;
  target_value?: number;
  actual_value?: number;
  unit?: string;
  target_date?: string;
  measured_at?: string;
  status: 'pending' | 'in_progress' | 'achieved' | 'missed' | 'partial';
  notes?: string;
  data_source?: string;
  created_at: string;
  updated_at: string;
  projects?: { id: string; title: string; current_phase?: string };
}

export interface OutcomeCreateRequest {
  project_id: string;
  title: string;
  description?: string;
  metric_type: string;
  baseline_value?: number;
  target_value?: number;
  unit?: string;
  target_date?: string;
  notes?: string;
  data_source?: string;
}

export interface OutcomeUpdateRequest {
  title?: string;
  description?: string;
  baseline_value?: number;
  target_value?: number;
  actual_value?: number;
  unit?: string;
  target_date?: string;
  status?: string;
  notes?: string;
  data_source?: string;
}

export interface OutcomeMeasurementRequest {
  actual_value: number;
  notes?: string;
}

export interface OutcomeSummary {
  total: number;
  achieved: number;
  in_progress: number;
  pending: number;
  achievement_rate: number;
}

export interface MetricType {
  id: string;
  name: string;
  description: string;
  unit: string;
  example: string;
}

/**
 * Create a new learning outcome
 */
export async function createOutcome(request: OutcomeCreateRequest): Promise<{
  success: boolean;
  outcome: LearningOutcome;
}> {
  return apiPost('/api/outcomes/create', request);
}

/**
 * Get all outcomes for a project
 */
export async function getProjectOutcomes(projectId: string): Promise<{
  success: boolean;
  project: { id: string; title: string };
  outcomes: LearningOutcome[];
  summary: OutcomeSummary;
}> {
  return apiGet(`/api/outcomes/project/${projectId}`);
}

/**
 * Get a specific outcome
 */
export async function getOutcome(outcomeId: string): Promise<{
  success: boolean;
  outcome: LearningOutcome;
}> {
  return apiGet(`/api/outcomes/${outcomeId}`);
}

/**
 * Update an outcome
 */
export async function updateOutcome(
  outcomeId: string,
  request: OutcomeUpdateRequest
): Promise<{ success: boolean; outcome: LearningOutcome }> {
  return apiPatch(`/api/outcomes/${outcomeId}`, request);
}

/**
 * Record a measurement for an outcome
 */
export async function recordOutcomeMeasurement(
  outcomeId: string,
  request: OutcomeMeasurementRequest
): Promise<{ success: boolean; outcome: LearningOutcome; status: string }> {
  return apiPost(`/api/outcomes/${outcomeId}/measure`, request);
}

/**
 * Delete an outcome
 */
export async function deleteOutcome(outcomeId: string): Promise<{ success: boolean; message: string }> {
  return apiDelete(`/api/outcomes/${outcomeId}`);
}

/**
 * Get outcomes dashboard summary
 */
export async function getOutcomesDashboard(): Promise<{
  success: boolean;
  summary: {
    total_outcomes: number;
    achieved: number;
    in_progress: number;
    pending: number;
    missed: number;
    partial: number;
    achievement_rate: number;
    average_progress: number;
  };
  by_metric_type: Record<string, { total: number; achieved: number }>;
  recent_outcomes: LearningOutcome[];
}> {
  return apiGet('/api/outcomes/dashboard/summary');
}

/**
 * Get available metric types
 */
export async function getMetricTypes(): Promise<{
  success: boolean;
  metric_types: MetricType[];
}> {
  return apiGet('/api/outcomes/metric-types');
}
