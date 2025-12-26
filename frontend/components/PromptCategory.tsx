'use client';

import { useState } from 'react';

interface QuickPrompt {
  id: string;
  prompt_text: string;
  addie_phase?: string;
  category?: string;
  usage_count: number;
  active: boolean;
  relevance_score?: number;
}

interface PromptCategoryProps {
  phase: string;
  prompts: QuickPrompt[];
  onPromptClick: (promptText: string) => void;
  isActive?: boolean;
  onToggleExpanded?: () => void;
  isExpanded?: boolean;
}

// Phase colors and icons - matching the filter tabs
const PHASE_CONFIG: Record<string, { color: string; bgColor: string; icon: string; description: string }> = {
  Analysis: {
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    icon: 'A',
    description: 'Identify needs and define problems'
  },
  Design: {
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    icon: 'D',
    description: 'Create learning objectives and strategies'
  },
  Development: {
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    icon: 'Dv',
    description: 'Build content and materials'
  },
  Implementation: {
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    icon: 'I',
    description: 'Deploy and deliver learning'
  },
  Evaluation: {
    color: 'text-pink-800',
    bgColor: 'bg-pink-100',
    icon: 'E',
    description: 'Measure impact and iterate'
  },
  General: {
    color: 'text-gray-700',
    bgColor: 'bg-gray-50',
    icon: 'G',
    description: 'Quick actions and commands'
  }
};

export default function PromptCategory({
  phase,
  prompts,
  onPromptClick,
  isActive = false,
  onToggleExpanded,
  isExpanded = true
}: PromptCategoryProps) {
  const config = PHASE_CONFIG[phase] || PHASE_CONFIG.General;
  const [localExpanded, setLocalExpanded] = useState(isExpanded);

  const handleToggle = () => {
    if (onToggleExpanded) {
      onToggleExpanded();
    } else {
      setLocalExpanded(!localExpanded);
    }
  };

  const expanded = onToggleExpanded !== undefined ? isExpanded : localExpanded;

  if (prompts.length === 0) {
    return null;
  }

  return (
    <div className={`prompt-category mb-3 rounded-lg border ${isActive ? 'border-primary-400 shadow-md' : 'border-default'} overflow-hidden transition-all`}>
      {/* Category Header */}
      <button
        onClick={handleToggle}
        className={`w-full px-4 py-2.5 flex items-center justify-between ${config.bgColor} hover:opacity-80 transition-opacity`}
      >
        <div className="flex items-center gap-2">
          <span className={`text-sm font-bold ${config.color} w-6 h-6 flex items-center justify-center rounded`} aria-hidden="true">{config.icon}</span>
          <div className="text-left">
            <h4 className={`text-sm font-semibold ${config.color}`}>
              {phase}
              {isActive && <span className="ml-2 text-xs font-normal">(Active)</span>}
            </h4>
            <p className="text-xs text-muted">{config.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-secondary bg-white px-2 py-0.5 rounded-full">
            {prompts.length}
          </span>
          <svg
            className={`w-4 h-4 ${config.color} transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Prompts List */}
      {expanded && (
        <div className="p-3 bg-card space-y-2">
          {prompts.map((prompt) => (
            <button
              key={prompt.id}
              className={`w-full text-left px-3 py-2 rounded-md text-sm transition-all
                ${prompt.relevance_score
                  ? 'bg-primary-100 border border-primary-300 text-primary-900 hover:bg-primary-200'
                  : 'bg-hover hover:bg-primary-50 text-primary border border-transparent hover:border-primary-200'
                }
              `}
              onClick={() => onPromptClick(prompt.prompt_text)}
              title={prompt.category ? `Category: ${prompt.category}` : undefined}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="flex-1">{prompt.prompt_text}</span>
                {prompt.relevance_score && prompt.relevance_score > 0 && (
                  <span className="flex-shrink-0 text-xs bg-primary-600 text-white px-1.5 py-0.5 rounded-full">
                    {prompt.relevance_score}
                  </span>
                )}
              </div>
              {prompt.category && (
                <div className="mt-1 text-xs text-muted">
                  {prompt.category}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
