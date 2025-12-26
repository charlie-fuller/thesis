'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from '@/components/LoadingSpinner';

interface InstructionVersion {
  id: string;
  agent_id: string;
  version_number: string;
  instructions: string;
  description: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  activated_at: string | null;
}

interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  system_instruction: string | null;
  is_active: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface Document {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  uploaded_at: string;
}

interface KBDocument {
  link_id: string;
  document: Document;
  notes: string | null;
  priority: number;
  added_at: string;
}

interface AgentData {
  agent: Agent;
  active_instruction_version: InstructionVersion | null;
  instruction_versions: InstructionVersion[];
  kb_documents: KBDocument[];
  stats: {
    conversations_count: number;
    instruction_versions_count: number;
    kb_documents_count: number;
  };
}

type TabType = 'instructions' | 'knowledge' | 'config' | 'stats';

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [data, setData] = useState<AgentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('instructions');

  // Instruction editing state
  const [editingInstructions, setEditingInstructions] = useState(false);
  const [newInstructions, setNewInstructions] = useState('');
  const [versionDescription, setVersionDescription] = useState('');
  const [saving, setSaving] = useState(false);

  // Knowledge base state
  const [showDocPicker, setShowDocPicker] = useState(false);
  const [availableDocs, setAvailableDocs] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  useEffect(() => {
    fetchAgent();
  }, [agentId]);

  const fetchAgent = async () => {
    try {
      setLoading(true);
      const result = await apiGet<AgentData>(`/api/agents/${agentId}`);
      setData(result);
      setNewInstructions(result.agent.system_instruction || '');
    } catch (err) {
      logger.error('Failed to fetch agent:', err);
      setError('Failed to load agent');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveInstructions = async () => {
    if (!newInstructions.trim()) return;

    try {
      setSaving(true);
      // Create new version
      const result = await apiPost<{ version: InstructionVersion }>(
        `/api/agents/${agentId}/instructions`,
        {
          instructions: newInstructions,
          description: versionDescription || null,
        }
      );

      // Activate it immediately
      await apiPost(`/api/agents/${agentId}/instructions/${result.version.id}/activate`, {});

      // Refresh data
      await fetchAgent();
      setEditingInstructions(false);
      setVersionDescription('');
    } catch (err) {
      logger.error('Failed to save instructions:', err);
      alert('Failed to save instructions');
    } finally {
      setSaving(false);
    }
  };

  const handleActivateVersion = async (versionId: string) => {
    try {
      await apiPost(`/api/agents/${agentId}/instructions/${versionId}/activate`, {});
      await fetchAgent();
    } catch (err) {
      logger.error('Failed to activate version:', err);
      alert('Failed to activate version');
    }
  };

  const handleToggleActive = async () => {
    if (!data) return;
    try {
      await apiPatch(`/api/agents/${agentId}`, {
        is_active: !data.agent.is_active,
      });
      await fetchAgent();
    } catch (err) {
      logger.error('Failed to toggle agent status:', err);
    }
  };

  const fetchAvailableDocs = async () => {
    try {
      setLoadingDocs(true);
      const result = await apiGet<{ documents: Document[] }>(`/api/agents/documents/available?agent_id=${agentId}`);
      setAvailableDocs(result.documents);
    } catch (err) {
      logger.error('Failed to fetch available documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleLinkDocument = async (documentId: string) => {
    try {
      await apiPost(`/api/agents/${agentId}/documents`, {
        document_id: documentId,
        priority: 0,
      });
      await fetchAgent();
      setShowDocPicker(false);
    } catch (err) {
      logger.error('Failed to link document:', err);
      alert('Failed to link document');
    }
  };

  const handleUnlinkDocument = async (linkId: string) => {
    if (!confirm('Remove this document from the agent knowledge base?')) return;
    try {
      await apiDelete(`/api/agents/${agentId}/documents/${linkId}`);
      await fetchAgent();
    } catch (err) {
      logger.error('Failed to unlink document:', err);
      alert('Failed to unlink document');
    }
  };

  const openDocPicker = () => {
    fetchAvailableDocs();
    setShowDocPicker(true);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getAgentIcon = (name: string) => {
    const icons: Record<string, string> = {
      atlas: '\u{1F30D}',
      fortuna: '\u{1F4B0}',
      guardian: '\u{1F6E1}',
      counselor: '\u{2696}',
      oracle: '\u{1F52E}',
    };
    return icons[name] || '\u{1F916}';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-20">
        <p className="text-red-400">{error || 'Agent not found'}</p>
        <Link href="/admin/agents" className="mt-4 btn-secondary inline-block">
          Back to Agents
        </Link>
      </div>
    );
  }

  const { agent, active_instruction_version, instruction_versions, kb_documents, stats } = data;

  return (
    <div>
      {/* Back Link */}
      <Link
        href="/admin/agents"
        className="text-secondary hover:text-primary text-sm mb-4 inline-flex items-center gap-1"
      >
        <span>&larr;</span> Back to Agents
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-xl bg-card border border-border flex items-center justify-center text-3xl">
            {getAgentIcon(agent.name)}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-primary">{agent.display_name}</h1>
            <p className="text-secondary">{agent.name}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleToggleActive}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              agent.is_active
                ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                : 'bg-gray-500/20 text-gray-400 hover:bg-gray-500/30'
            }`}
          >
            {agent.is_active ? 'Active' : 'Inactive'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border mb-6">
        {(['instructions', 'knowledge', 'config', 'stats'] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors capitalize ${
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            {tab === 'knowledge' ? 'Knowledge Base' : tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'instructions' && (
        <div className="space-y-6">
          {/* Current Instructions */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-primary">System Instructions</h2>
              {active_instruction_version && (
                <span className="text-sm text-secondary">
                  Version {active_instruction_version.version_number}
                </span>
              )}
            </div>

            {editingInstructions ? (
              <div className="space-y-4">
                <textarea
                  value={newInstructions}
                  onChange={(e) => setNewInstructions(e.target.value)}
                  className="w-full h-96 px-4 py-3 bg-page border border-border rounded-lg text-primary font-mono text-sm resize-y focus:outline-none focus:border-primary"
                  placeholder="Enter system instructions..."
                />
                <input
                  type="text"
                  value={versionDescription}
                  onChange={(e) => setVersionDescription(e.target.value)}
                  placeholder="Version description (optional)"
                  className="w-full px-4 py-2 bg-page border border-border rounded-lg text-primary text-sm focus:outline-none focus:border-primary"
                />
                <div className="flex gap-3">
                  <button
                    onClick={handleSaveInstructions}
                    disabled={saving}
                    className="btn-primary"
                  >
                    {saving ? 'Saving...' : 'Save & Activate'}
                  </button>
                  <button
                    onClick={() => {
                      setEditingInstructions(false);
                      setNewInstructions(agent.system_instruction || '');
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <pre className="bg-page p-4 rounded-lg text-sm text-secondary overflow-auto max-h-96 whitespace-pre-wrap font-mono">
                  {agent.system_instruction || 'No instructions configured'}
                </pre>
                <button
                  onClick={() => setEditingInstructions(true)}
                  className="mt-4 btn-primary"
                >
                  Edit Instructions
                </button>
              </div>
            )}
          </div>

          {/* Version History */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-primary mb-4">Version History</h2>
            {instruction_versions.length === 0 ? (
              <p className="text-secondary text-sm">No version history yet</p>
            ) : (
              <div className="space-y-3">
                {instruction_versions.map((version) => (
                  <div
                    key={version.id}
                    className={`p-4 rounded-lg border ${
                      version.is_active
                        ? 'border-primary bg-primary/5'
                        : 'border-border bg-page'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium text-primary">
                          v{version.version_number}
                        </span>
                        {version.is_active && (
                          <span className="ml-2 text-xs bg-primary/20 text-primary px-2 py-0.5 rounded">
                            Active
                          </span>
                        )}
                        {version.description && (
                          <p className="text-sm text-secondary mt-1">{version.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-secondary">
                          {new Date(version.created_at).toLocaleDateString()}
                        </span>
                        {!version.is_active && (
                          <button
                            onClick={() => handleActivateVersion(version.id)}
                            className="text-xs text-primary hover:underline"
                          >
                            Activate
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'knowledge' && (
        <div className="space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-primary">Knowledge Base Documents</h2>
                <p className="text-secondary text-sm mt-1">
                  These documents will be used for RAG retrieval when this agent responds.
                </p>
              </div>
              <button onClick={openDocPicker} className="btn-primary">
                + Add Document
              </button>
            </div>

            {kb_documents.length === 0 ? (
              <div className="text-center py-12 bg-page rounded-lg border border-dashed border-border">
                <p className="text-secondary">No documents linked yet</p>
                <p className="text-sm text-muted mt-2">
                  Add documents to give this agent specialized knowledge
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {kb_documents.map((kbDoc) => (
                  <div
                    key={kbDoc.link_id}
                    className="flex items-center justify-between p-4 bg-page rounded-lg border border-border"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-card border border-border flex items-center justify-center text-lg">
                        {kbDoc.document.content_type?.includes('pdf') ? '📄' :
                         kbDoc.document.content_type?.includes('word') ? '📝' :
                         kbDoc.document.content_type?.includes('text') ? '📃' : '📁'}
                      </div>
                      <div>
                        <p className="font-medium text-primary">{kbDoc.document.filename}</p>
                        <p className="text-xs text-secondary">
                          {formatFileSize(kbDoc.document.file_size)} • Added {new Date(kbDoc.added_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleUnlinkDocument(kbDoc.link_id)}
                      className="text-sm text-red-400 hover:text-red-300"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Document Picker Modal */}
          {showDocPicker && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <div className="bg-card rounded-xl border border-border p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-primary">Add Document to Knowledge Base</h3>
                  <button
                    onClick={() => setShowDocPicker(false)}
                    className="text-secondary hover:text-primary"
                  >
                    ✕
                  </button>
                </div>

                {loadingDocs ? (
                  <div className="py-12 text-center">
                    <LoadingSpinner size="md" />
                    <p className="text-secondary mt-2">Loading documents...</p>
                  </div>
                ) : availableDocs.length === 0 ? (
                  <div className="py-12 text-center">
                    <p className="text-secondary">No available documents</p>
                    <p className="text-sm text-muted mt-2">
                      All documents are already linked or no documents have been uploaded yet.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-y-auto flex-1 space-y-2">
                    {availableDocs.map((doc) => (
                      <button
                        key={doc.id}
                        onClick={() => handleLinkDocument(doc.id)}
                        className="w-full flex items-center gap-3 p-3 bg-page rounded-lg border border-border hover:border-primary transition-colors text-left"
                      >
                        <div className="w-10 h-10 rounded-lg bg-card border border-border flex items-center justify-center text-lg">
                          {doc.content_type?.includes('pdf') ? '📄' :
                           doc.content_type?.includes('word') ? '📝' :
                           doc.content_type?.includes('text') ? '📃' : '📁'}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-primary truncate">{doc.filename}</p>
                          <p className="text-xs text-secondary">
                            {formatFileSize(doc.file_size)} • {new Date(doc.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                        <span className="text-primary text-sm">+ Add</span>
                      </button>
                    ))}
                  </div>
                )}

                <div className="mt-4 pt-4 border-t border-border">
                  <button
                    onClick={() => setShowDocPicker(false)}
                    className="btn-secondary w-full"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'config' && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-primary mb-4">Configuration</h2>
          <div className="space-y-6">
            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-primary mb-2">
                Description
              </label>
              <p className="text-secondary text-sm">
                {agent.description || 'No description set'}
              </p>
            </div>

            {/* Config JSON */}
            <div>
              <label className="block text-sm font-medium text-primary mb-2">
                Agent Config
              </label>
              <pre className="bg-page p-4 rounded-lg text-sm text-secondary overflow-auto font-mono">
                {JSON.stringify(agent.config, null, 2)}
              </pre>
            </div>

            {/* Timestamps */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
              <div>
                <label className="block text-xs text-secondary mb-1">Created</label>
                <p className="text-sm text-primary">
                  {new Date(agent.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <label className="block text-xs text-secondary mb-1">Last Updated</label>
                <p className="text-sm text-primary">
                  {new Date(agent.updated_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-6">
            <div className="card p-6 text-center">
              <div className="text-4xl font-bold text-primary mb-2">
                {stats.conversations_count}
              </div>
              <div className="text-secondary">Total Conversations</div>
            </div>
            <div className="card p-6 text-center">
              <div className="text-4xl font-bold text-primary mb-2">
                {stats.instruction_versions_count}
              </div>
              <div className="text-secondary">Instruction Versions</div>
            </div>
            <div className="card p-6 text-center">
              <div className="text-4xl font-bold text-primary mb-2">
                {stats.kb_documents_count || kb_documents.length}
              </div>
              <div className="text-secondary">KB Documents</div>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold text-primary mb-4">Recent Activity</h2>
            <p className="text-secondary text-sm">
              Detailed analytics coming soon
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
