'use client';

import { useState, useEffect, useCallback } from 'react';
import { X, BookmarkPlus, Globe, Users } from 'lucide-react';
import { apiGet } from '@/lib/api';
import { AgentIcon, getAgentColor } from './AgentIcon';

interface Agent {
  id: string;
  name: string;
  display_name: string;
}

interface SaveToKBModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (title: string, agentIds: string[] | null) => Promise<void>;
  defaultTitle?: string;
  isSaving?: boolean;
}

export default function SaveToKBModal({
  isOpen,
  onClose,
  onSave,
  defaultTitle = '',
  isSaving = false
}: SaveToKBModalProps) {
  const [title, setTitle] = useState(defaultTitle);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentIds, setSelectedAgentIds] = useState<Set<string>>(new Set());
  const [isGlobal, setIsGlobal] = useState(true);
  const [loadingAgents, setLoadingAgents] = useState(false);

  // Load agents when modal opens
  useEffect(() => {
    if (isOpen) {
      loadAgents();
      setTitle(defaultTitle);
      setIsGlobal(true);
      setSelectedAgentIds(new Set());
    }
  }, [isOpen, defaultTitle]);

  async function loadAgents() {
    try {
      setLoadingAgents(true);
      const data = await apiGet<{ agents: Agent[] }>('/api/agents?include_inactive=false');
      setAgents(data.agents || []);
    } catch (err) {
      console.error('Failed to load agents:', err);
    } finally {
      setLoadingAgents(false);
    }
  }

  function toggleAgentSelection(agentId: string) {
    setSelectedAgentIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(agentId)) {
        newSet.delete(agentId);
      } else {
        newSet.add(agentId);
      }
      return newSet;
    });
  }

  const handleSave = useCallback(async () => {
    if (!title.trim()) return;

    const agentIds = isGlobal ? null : Array.from(selectedAgentIds);
    await onSave(title.trim(), agentIds);
  }, [title, isGlobal, selectedAgentIds, onSave]);

  const canSave = title.trim() && (isGlobal || selectedAgentIds.size > 0);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-primary rounded-lg shadow-xl w-full max-w-md mx-4 p-6 border border-default">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BookmarkPlus className="h-5 w-5 text-brand" />
            <h2 className="text-lg font-semibold text-primary">Save to Knowledge Base</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-hover rounded-md transition-colors"
          >
            <X className="h-5 w-5 text-muted" />
          </button>
        </div>

        {/* Title input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-primary mb-1">
            Document Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a title for this document..."
            className="w-full px-3 py-2 bg-secondary border border-default rounded-md text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
            autoFocus
          />
        </div>

        {/* Scope selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-primary mb-2">
            Document Availability
          </label>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setIsGlobal(true)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors ${
                isGlobal
                  ? 'bg-brand/10 border-brand text-brand'
                  : 'bg-secondary border-default text-muted hover:border-brand/50'
              }`}
            >
              <Globe className="h-4 w-4" />
              <span className="text-sm font-medium">Global</span>
            </button>
            <button
              type="button"
              onClick={() => setIsGlobal(false)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors ${
                !isGlobal
                  ? 'bg-brand/10 border-brand text-brand'
                  : 'bg-secondary border-default text-muted hover:border-brand/50'
              }`}
            >
              <Users className="h-4 w-4" />
              <span className="text-sm font-medium">Agent-specific</span>
            </button>
          </div>

          <p className="text-xs text-muted mt-2">
            {isGlobal
              ? 'All agents will be able to access this document.'
              : 'Only selected agents will be able to access this document.'}
          </p>
        </div>

        {/* Agent selection (only shown when agent-specific is selected) */}
        {!isGlobal && (
          <div className="mb-4 p-3 bg-tertiary rounded-lg border border-default">
            <p className="text-xs text-muted mb-2">Select agents:</p>
            {loadingAgents ? (
              <div className="flex items-center gap-2 text-sm text-muted py-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand"></div>
                Loading agents...
              </div>
            ) : agents.length === 0 ? (
              <p className="text-sm text-muted py-2">No agents available</p>
            ) : (
              <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                {agents.map(agent => (
                  <label
                    key={agent.id}
                    className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                      selectedAgentIds.has(agent.id)
                        ? 'bg-brand/10 border-brand'
                        : 'bg-secondary border-default hover:border-brand/50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedAgentIds.has(agent.id)}
                      onChange={() => toggleAgentSelection(agent.id)}
                      className="sr-only"
                    />
                    <div className={`w-5 h-5 rounded flex items-center justify-center ${getAgentColor(agent.name)}`}>
                      <AgentIcon name={agent.name} size="sm" />
                    </div>
                    <span className="text-sm text-primary truncate">{agent.display_name}</span>
                  </label>
                ))}
              </div>
            )}
            {selectedAgentIds.size === 0 && agents.length > 0 && (
              <p className="text-xs text-amber-600 mt-2">
                Select at least one agent, or choose &quot;Global&quot;.
              </p>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={isSaving}
            className="flex-1 px-4 py-2 text-sm font-medium text-muted bg-secondary hover:bg-hover border border-default rounded-md transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!canSave || isSaving}
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand/90 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Saving...
              </>
            ) : (
              <>
                <BookmarkPlus className="h-4 w-4" />
                Save
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
