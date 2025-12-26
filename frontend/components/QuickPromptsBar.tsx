'use client';

import { useState, useEffect } from 'react';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';
import PromptCategory from './PromptCategory';

interface QuickPrompt {
  id: string;
  prompt_text: string;
  function_name?: string;
  addie_phase?: string;
  category?: string;
  contextual_keywords?: string[];
  usage_count: number;
  active: boolean;
  display_order?: number;
  relevance_score?: number;
}

interface QuickPromptsBarProps {
  onPromptClick: (promptText: string) => void;
  conversationText?: string; // Recent conversation for contextual suggestions
  uploadedDocuments?: number; // Number of uploaded documents
}

type ViewMode = 'all' | 'contextual' | 'phase';
type ADDIEPhase = 'Analysis' | 'Design' | 'Development' | 'Implementation' | 'Evaluation' | 'General';
type PhaseFilter = 'All' | ADDIEPhase;

export default function QuickPromptsBar({
  onPromptClick,
  conversationText = '',
  uploadedDocuments = 0
}: QuickPromptsBarProps) {
  const [prompts, setPrompts] = useState<QuickPrompt[]>([]);
  const [contextualPrompts, setContextualPrompts] = useState<QuickPrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('all');
  const [selectedPhase, setSelectedPhase] = useState<PhaseFilter>('All');
  const [detectedPhase, setDetectedPhase] = useState<ADDIEPhase | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set(['Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'General']));

  useEffect(() => {
    fetchQuickPrompts();
  }, []);

  // Fetch contextual prompts when conversation text changes
  useEffect(() => {
    if (conversationText && conversationText.length > 50) {
      fetchContextualPrompts(conversationText);
      detectPhaseFromConversation(conversationText);
    }
  }, [conversationText]);

  const fetchQuickPrompts = async () => {
    try {
      const response = await apiGet<{ success: boolean; prompts: QuickPrompt[] }>('/api/quick-prompts?active_only=true');
      if (response.success) {
        setPrompts(response.prompts || []);
      }
    } catch (error) {
      logger.error('Error fetching quick prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchContextualPrompts = async (text: string) => {
    try {
      const response = await apiPost<{ success: boolean; prompts: QuickPrompt[] }>('/api/quick-prompts/contextual', {
        conversation_text: text,
        limit: 5
      });
      if (response.success && response.prompts.length > 0) {
        setContextualPrompts(response.prompts);
      }
    } catch (error) {
      logger.error('Error fetching contextual prompts:', error);
    }
  };

  const detectPhaseFromConversation = async (text: string) => {
    try {
      const response = await apiPost<{ success: boolean; detected_phase: string }>('/api/quick-prompts/detect-phase', {
        conversation_text: text
      });
      if (response.success) {
        setDetectedPhase(response.detected_phase as ADDIEPhase);
        // Auto-expand detected phase
        setExpandedPhases(prev => new Set([...prev, response.detected_phase]));
      }
    } catch (error) {
      logger.error('Error detecting phase:', error);
    }
  };

  const handlePromptClick = async (prompt: QuickPrompt) => {
    // Track usage
    try {
      await apiPost(`/api/quick-prompts/${prompt.id}/use`, {});
    } catch (error) {
      logger.error('Error tracking prompt usage:', error);
    }

    // Send message
    onPromptClick(prompt.prompt_text);
  };

  const togglePhaseExpansion = (phase: string) => {
    setExpandedPhases(prev => {
      const newSet = new Set(prev);
      if (newSet.has(phase)) {
        newSet.delete(phase);
      } else {
        newSet.add(phase);
      }
      return newSet;
    });
  };

  const handlePhaseFilterChange = (phase: PhaseFilter) => {
    setSelectedPhase(phase);
    // If a specific phase is selected, expand only that phase
    if (phase !== 'All') {
      setExpandedPhases(new Set([phase]));
    } else {
      // Expand all phases when "All" is selected
      setExpandedPhases(new Set(['Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'General']));
    }
  };

  if (loading) {
    return (
      <div className="quick-prompts-bar py-2">
        <div className="text-xs text-muted">Loading quick prompts...</div>
      </div>
    );
  }

  if (prompts.length === 0) {
    return null; // Don't show if no prompts
  }

  // Group prompts by ADDIE phase
  const promptsByPhase: Record<string, QuickPrompt[]> = {};
  const phases: ADDIEPhase[] = ['Analysis', 'Design', 'Development', 'Implementation', 'Evaluation', 'General'];

  phases.forEach(phase => {
    promptsByPhase[phase] = prompts.filter(p => p.addie_phase === phase);
  });

  // Legacy prompts without phase
  const legacyPrompts = prompts.filter(p => !p.addie_phase);

  // Filter phases based on selected filter
  const visiblePhases = selectedPhase === 'All'
    ? phases.filter(phase => promptsByPhase[phase]?.length > 0)
    : phases.filter(phase => phase === selectedPhase && promptsByPhase[phase]?.length > 0);

  return (
    <div className="quick-prompts-bar mb-4">
      {/* Header with view mode toggle */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-primary">
          L&D Quick Prompts
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('all')}
            className={`text-xs px-2 py-1 rounded ${viewMode === 'all' ? 'bg-primary text-white' : 'text-secondary hover:bg-hover'}`}
          >
            All Phases
          </button>
          {contextualPrompts.length > 0 && (
            <button
              onClick={() => setViewMode('contextual')}
              className={`text-xs px-2 py-1 rounded ${viewMode === 'contextual' ? 'bg-primary text-white' : 'text-secondary hover:bg-hover'} relative`}
            >
              Contextual
              <span className="ml-1 bg-green-500 text-white text-xs rounded-full px-1.5 py-0.5">
                {contextualPrompts.length}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Phase Filter Tabs */}
      {viewMode === 'all' && (
        <div className="flex gap-1 flex-wrap mb-3">
          {(['All', 'Analysis', 'Design', 'Development', 'Implementation', 'Evaluation'] as PhaseFilter[]).map((phase) => {
            const phasePrompts = phase === 'All'
              ? prompts.filter(p => p.addie_phase)
              : promptsByPhase[phase as ADDIEPhase] || [];

            if (phase !== 'All' && phasePrompts.length === 0) return null;

            return (
              <button
                key={phase}
                onClick={() => handlePhaseFilterChange(phase)}
                className={`text-xs px-3 py-1.5 rounded-full transition-all ${
                  selectedPhase === phase
                    ? phase === 'All'
                      ? 'bg-gray-700 text-white'
                      : phase === 'Analysis'
                      ? 'bg-green-600 text-white'
                      : phase === 'Design'
                      ? 'bg-blue-600 text-white'
                      : phase === 'Development'
                      ? 'bg-purple-600 text-white'
                      : phase === 'Implementation'
                      ? 'bg-orange-600 text-white'
                      : phase === 'Evaluation'
                      ? 'bg-pink-600 text-white'
                      : 'bg-gray-600 text-white'
                    : phase === 'All'
                    ? 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    : phase === 'Analysis'
                    ? 'bg-green-100 text-green-800 hover:bg-green-200'
                    : phase === 'Design'
                    ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                    : phase === 'Development'
                    ? 'bg-purple-100 text-purple-800 hover:bg-purple-200'
                    : phase === 'Implementation'
                    ? 'bg-orange-100 text-orange-800 hover:bg-orange-200'
                    : phase === 'Evaluation'
                    ? 'bg-pink-100 text-pink-800 hover:bg-pink-200'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                }`}
              >
                {phase}
                {phase !== 'All' && (
                  <span className="ml-1 font-semibold">
                    ({phasePrompts.length})
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Phase detection indicator */}
      {detectedPhase && viewMode === 'all' && (
        <div className="mb-3 p-2 bg-primary-50 border border-primary-200 rounded-md">
          <p className="text-xs text-primary">
            <span className="font-medium">Detected Phase:</span> {detectedPhase}
          </p>
        </div>
      )}

      {/* Document upload prompt */}
      {uploadedDocuments > 0 && (
        <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded-md">
          <button
            onClick={() => onPromptClick('Summarize this document for learning design')}
            className="text-xs text-green-700 hover:underline w-full text-left"
          >
            Analyze uploaded document for L&D ({uploadedDocuments} file{uploadedDocuments > 1 ? 's' : ''})
          </button>
        </div>
      )}

      {/* Contextual View */}
      {viewMode === 'contextual' && contextualPrompts.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted mb-2">Based on your conversation:</p>
          {contextualPrompts.map((prompt) => (
            <button
              key={prompt.id}
              className="w-full text-left px-3 py-2 rounded-md bg-primary-100 border border-primary-300 text-primary-900 hover:bg-primary-200 text-sm transition-all"
              onClick={() => handlePromptClick(prompt)}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="flex-1">{prompt.prompt_text}</span>
                {prompt.relevance_score && (
                  <span className="flex-shrink-0 text-xs bg-primary-600 text-white px-1.5 py-0.5 rounded-full">
                    {prompt.relevance_score}
                  </span>
                )}
              </div>
              {prompt.addie_phase && (
                <div className="mt-1 text-xs text-primary-700">
                  {prompt.addie_phase} - {prompt.category}
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {/* ADDIE Phases View */}
      {viewMode === 'all' && (
        <div className="space-y-2">
          {visiblePhases.map(phase => {
            const phasePrompts = promptsByPhase[phase] || [];
            if (phasePrompts.length === 0) return null;

            return (
              <PromptCategory
                key={phase}
                phase={phase}
                prompts={phasePrompts}
                onPromptClick={onPromptClick}
                isActive={detectedPhase === phase}
                isExpanded={expandedPhases.has(phase)}
                onToggleExpanded={() => togglePhaseExpansion(phase)}
              />
            );
          })}

          {/* Legacy prompts (for backward compatibility) */}
          {legacyPrompts.length > 0 && selectedPhase === 'All' && (
            <div className="mt-3 p-3 bg-gray-50 rounded-md">
              <p className="text-xs text-muted mb-2">Other Prompts:</p>
              <div className="flex flex-wrap gap-2">
                {legacyPrompts.map((prompt) => (
                  <button
                    key={prompt.id}
                    className="prompt-chip px-3 py-1.5 rounded-full bg-primary-50 hover:bg-primary-100 text-primary text-sm transition-all hover:shadow-sm border border-primary-200 hover:border-primary-300"
                    onClick={() => handlePromptClick(prompt)}
                  >
                    {prompt.prompt_text}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
