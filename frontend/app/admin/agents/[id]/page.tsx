'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { Upload, FileText, X } from 'lucide-react';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from '@/components/LoadingSpinner';
import { AgentIcon, getAgentColor } from '@/components/AgentIcon';

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

interface CompareResponse {
  success: boolean;
  version_a: { id: string; version_number: string; created_at: string };
  version_b: { id: string; version_number: string; created_at: string };
  diff: string[];
  stats: {
    additions: number;
    deletions: number;
    total_changes: number;
  };
}

interface SummaryResponse {
  success: boolean;
  version_a: { id: string; version_number: string; created_at: string };
  version_b: { id: string; version_number: string; created_at: string };
  summary: string;
  stats: {
    additions: number;
    deletions: number;
    total_changes: number;
  };
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

interface DefaultInstructionsResponse {
  success: boolean;
  has_default: boolean;
  agent_name: string;
  display_name: string;
  default_instructions: string;
  character_count: number;
  word_count: number;
}

interface XmlInstructionsResponse {
  success: boolean;
  has_xml: boolean;
  agent_name: string;
  display_name: string;
  xml_instructions: string;
  character_count: number;
  word_count: number;
  file_modified_at: string | null;
}

// Helper to detect placeholder text in instructions
function isPlaceholderInstruction(instruction: string | null | undefined): boolean {
  if (!instruction) return true;
  if (instruction.trim().length < 100) return true;
  if (instruction.trim().startsWith('--')) return true;
  return false;
}

type TabType = 'overview' | 'instructions' | 'compare' | 'knowledge' | 'config' | 'stats';

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.id as string;

  const [data, setData] = useState<AgentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Instruction editing state
  const [editingInstructions, setEditingInstructions] = useState(false);
  const [editMode, setEditMode] = useState<'text' | 'upload'>('text');
  const [newInstructions, setNewInstructions] = useState('');
  const [versionDescription, setVersionDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; size: number; content: string } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Version comparison state
  const [compareVersionA, setCompareVersionA] = useState<string>('');
  const [compareVersionB, setCompareVersionB] = useState<string>('');
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [summaryResult, setSummaryResult] = useState<SummaryResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [generatingSummary, setGeneratingSummary] = useState(false);

  // Version viewing/deleting state
  const [viewingVersion, setViewingVersion] = useState<InstructionVersion | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Knowledge base state
  const [showDocPicker, setShowDocPicker] = useState(false);
  const [availableDocs, setAvailableDocs] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  // XML instructions state
  const [xmlInstructions, setXmlInstructions] = useState<string | null>(null);
  const [xmlModifiedAt, setXmlModifiedAt] = useState<string | null>(null);
  const [hasXmlFile, setHasXmlFile] = useState(false);
  const [loadingXml, setLoadingXml] = useState(false);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchAgent();
  }, [agentId]);

  const fetchAgent = async () => {
    try {
      setLoading(true);
      const result = await apiGet<AgentData>(`/api/agents/${agentId}`);
      setData(result);

      // Check if DB instructions are placeholder text
      const dbInstructions = result.active_instruction_version?.instructions || result.agent.system_instruction || '';
      const hasPlaceholder = isPlaceholderInstruction(dbInstructions);

      // Also fetch XML file info and get the instructions directly
      const xmlContent = await fetchXmlInstructions();

      // Determine which instructions to display
      if (hasPlaceholder && xmlContent) {
        // Use XML instructions if DB has placeholder
        setNewInstructions(xmlContent);
      } else if (!hasPlaceholder) {
        setNewInstructions(dbInstructions);
      } else if (xmlContent) {
        // Fallback to XML if available
        setNewInstructions(xmlContent);
      }
    } catch (err) {
      logger.error('Failed to fetch agent:', err);
      setError('Failed to load agent');
    } finally {
      setLoading(false);
    }
  };

  const fetchXmlInstructions = async (): Promise<string | null> => {
    try {
      setLoadingXml(true);
      const result = await apiGet<XmlInstructionsResponse>(`/api/agents/${agentId}/xml-instructions`);
      if (result.success && result.has_xml) {
        setXmlInstructions(result.xml_instructions);
        setXmlModifiedAt(result.file_modified_at);
        setHasXmlFile(true);
        return result.xml_instructions;
      } else {
        setHasXmlFile(false);
        return null;
      }
    } catch (err) {
      logger.error('Failed to fetch XML instructions:', err);
      setHasXmlFile(false);
      return null;
    } finally {
      setLoadingXml(false);
    }
  };

  const handleSyncFromXml = async () => {
    try {
      setSyncing(true);
      await apiPost(`/api/agents/${agentId}/sync-from-xml`, {
        description: 'Synced from XML file'
      });
      toast.success('Instructions synced from XML file');
      await fetchAgent();
    } catch (err) {
      logger.error('Failed to sync from XML:', err);
      toast.error('Failed to sync from XML file');
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncToXml = async () => {
    try {
      setSyncing(true);
      await apiPost(`/api/agents/${agentId}/sync-to-xml`, {});
      toast.success('Instructions saved to XML file');
      await fetchXmlInstructions();
    } catch (err) {
      logger.error('Failed to sync to XML:', err);
      toast.error('Failed to save to XML file');
    } finally {
      setSyncing(false);
    }
  };

  const handleDeployInstructions = async () => {
    if (!newInstructions.trim()) return;

    try {
      setSaving(true);

      // Create new version in database
      const result = await apiPost<{ version: InstructionVersion }>(
        `/api/agents/${agentId}/instructions`,
        {
          instructions: newInstructions,
          description: versionDescription || 'Updated via admin UI',
        }
      );

      // Activate it immediately
      await apiPost(`/api/agents/${agentId}/instructions/${result.version.id}/activate`, {});

      // Also sync to XML file to keep it as the source of truth
      try {
        await apiPost(`/api/agents/${agentId}/sync-to-xml`, {});
      } catch (xmlErr) {
        // XML sync is not critical, just log it
        logger.warn('Failed to sync to XML file:', xmlErr);
      }

      toast.success(`Instructions deployed as version ${result.version.version_number}`);

      // Refresh data
      await fetchAgent();
      setEditingInstructions(false);
      setVersionDescription('');
      setUploadedFile(null);
    } catch (err) {
      logger.error('Failed to deploy instructions:', err);
      toast.error('Failed to deploy instructions');
    } finally {
      setSaving(false);
    }
  };

  const handleActivateVersion = async (versionId: string) => {
    try {
      await apiPost(`/api/agents/${agentId}/instructions/${versionId}/activate`, {});
      toast.success('Version activated');
      await fetchAgent();
    } catch (err) {
      logger.error('Failed to activate version:', err);
      toast.error('Failed to activate version');
    }
  };

  const handleDeleteVersion = async (version: InstructionVersion) => {
    if (version.is_active) {
      toast.error('Cannot delete the active version');
      return;
    }

    if (!confirm(`Are you sure you want to delete version ${version.version_number}? This cannot be undone.`)) {
      return;
    }

    setDeleting(version.id);
    try {
      await apiDelete(`/api/agents/${agentId}/instructions/${version.id}`);
      toast.success(`Version ${version.version_number} deleted`);
      await fetchAgent();
    } catch (err) {
      logger.error('Failed to delete version:', err);
      toast.error('Failed to delete version');
    } finally {
      setDeleting(null);
    }
  };

  const handleViewVersion = async (versionId: string) => {
    try {
      const response = await apiGet<{ success: boolean; version: InstructionVersion }>(
        `/api/agents/${agentId}/instructions/${versionId}`
      );
      if (response.success) {
        setViewingVersion(response.version);
      }
    } catch (err) {
      logger.error('Failed to load version:', err);
      toast.error('Failed to load version details');
    }
  };

  const handleCompare = async () => {
    if (!compareVersionA || !compareVersionB) {
      toast.error('Please select two versions to compare');
      return;
    }

    if (compareVersionA === compareVersionB) {
      toast.error('Please select two different versions');
      return;
    }

    setComparing(true);
    setCompareResult(null);
    setSummaryResult(null);

    try {
      const response = await apiPost<CompareResponse>(
        `/api/agents/${agentId}/instructions/compare`,
        {
          version_a_id: compareVersionA,
          version_b_id: compareVersionB,
        }
      );

      if (response.success) {
        setCompareResult(response);
      }
    } catch (err) {
      logger.error('Compare error:', err);
      toast.error('Failed to compare versions');
    } finally {
      setComparing(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!compareVersionA || !compareVersionB) {
      toast.error('Please select two versions first');
      return;
    }

    setGeneratingSummary(true);

    try {
      const response = await apiPost<SummaryResponse>(
        `/api/agents/${agentId}/instructions/compare/summary`,
        {
          version_a_id: compareVersionA,
          version_b_id: compareVersionB,
        }
      );

      if (response.success) {
        setSummaryResult(response);
      }
    } catch (err) {
      logger.error('Summary generation error:', err);
      toast.error('Failed to generate AI summary');
    } finally {
      setGeneratingSummary(false);
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

  const handleFileSelect = (file: File) => {
    if (!file) return;

    const validExtensions = ['.txt', '.xml'];
    const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!validExtensions.includes(extension)) {
      toast.error('Please upload a .txt or .xml file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setUploadedFile({
        name: file.name,
        size: file.size,
        content,
      });
      setNewInstructions(content);
    };
    reader.onerror = () => {
      toast.error('Failed to read file');
    };
    reader.readAsText(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const clearUploadedFile = () => {
    setUploadedFile(null);
    setNewInstructions(data?.active_instruction_version?.instructions || data?.agent.system_instruction || '');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className={`w-16 h-16 rounded-xl flex items-center justify-center border ${getAgentColor(agent.name)}`}>
            <AgentIcon name={agent.name} size="lg" className="w-10 h-10" />
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
        {(['overview', 'instructions', 'compare', 'knowledge', 'config', 'stats'] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors capitalize ${
              activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-secondary hover:text-primary'
            }`}
          >
            {tab === 'knowledge' ? 'Knowledge Base' : tab === 'compare' ? 'Compare Versions' : tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Agent Purpose */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-primary mb-4">What This Agent Does</h2>
            <p className="text-secondary leading-relaxed">
              {agent.description || 'No description configured for this agent.'}
            </p>
          </div>

          {/* Agent Role & Capabilities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card p-6">
              <h3 className="text-md font-semibold text-primary mb-3">Why It Exists</h3>
              <p className="text-secondary text-sm leading-relaxed">
                {(() => {
                  const purposes: Record<string, string> = {
                    atlas: 'Provides research intelligence for GenAI implementation, leveraging Lean methodology and competitive benchmarking to support data-driven decisions.',
                    fortuna: 'Delivers financial analysis including ROI calculations, business case development, and SOX compliance considerations for AI investments.',
                    guardian: 'Ensures IT governance, security compliance, shadow IT detection, and vendor evaluation for enterprise AI deployments.',
                    counselor: 'Addresses legal considerations including contracts, AI risk assessment, liability, and data privacy compliance.',
                    oracle: 'Analyzes meeting transcripts to extract stakeholder insights, sentiment patterns, and strategic recommendations with evidence.',
                    sage: 'Focuses on change management, human flourishing, and driving successful AI adoption across the organization.',
                    strategist: 'Provides C-suite engagement strategies, navigates organizational politics, and designs governance frameworks.',
                    architect: 'Designs technical architecture for enterprise AI including RAG systems, integrations, and build vs. buy decisions.',
                    operator: 'Optimizes business processes, identifies automation opportunities, and tracks operational metrics.',
                    pioneer: 'Scouts emerging technologies, filters hype from reality, and assesses innovation maturity for practical application.',
                    catalyst: 'Crafts internal AI communications, addresses employee concerns, and builds engagement around AI initiatives.',
                    scholar: 'Develops training programs, enables AI champions, and applies adult learning principles for skill development.',
                    echo: 'Analyzes brand voice, creates style profiles, and provides guidelines for AI-assisted content that matches organizational tone.',
                    nexus: 'Maps interconnections between initiatives, identifies feedback loops, and surfaces unintended consequences in complex systems.',
                    coordinator: 'Orchestrates multi-agent collaboration, routes queries to specialists, and synthesizes responses across the platform.',
                  };
                  return purposes[agent.name.toLowerCase()] || 'This agent provides specialized capabilities within the Thesis platform.';
                })()}
              </p>
            </div>

            <div className="card p-6">
              <h3 className="text-md font-semibold text-primary mb-3">How To Use It</h3>
              <p className="text-secondary text-sm leading-relaxed">
                {(() => {
                  const howTo: Record<string, string> = {
                    atlas: 'Ask research questions about GenAI trends, request competitive analysis, or explore best practices. Atlas will search the web and knowledge base to provide sourced answers.',
                    fortuna: 'Request ROI projections, business case frameworks, or financial impact assessments. Provide context about the AI initiative for tailored analysis.',
                    guardian: 'Consult on security requirements, compliance frameworks, or vendor evaluations. Share technical details for more specific guidance.',
                    counselor: 'Ask about contract terms, regulatory compliance, or risk mitigation strategies. Include relevant context about stakeholders and jurisdictions.',
                    oracle: 'Upload meeting transcripts or recordings. Oracle will extract stakeholder positions, sentiment, and actionable insights with supporting quotes.',
                    sage: 'Discuss change management strategies, adoption challenges, or team dynamics. Sage helps design people-first AI implementation plans.',
                    strategist: 'Seek guidance on executive engagement, stakeholder navigation, or governance design. Share organizational context for strategic recommendations.',
                    architect: 'Discuss technical requirements, architecture patterns, or integration approaches. Provide system details for concrete recommendations.',
                    operator: 'Identify process optimization opportunities, automation candidates, or operational metrics. Share workflow details for analysis.',
                    pioneer: 'Explore emerging technologies, assess innovation maturity, or evaluate new tools. Pioneer separates signal from noise in the AI landscape.',
                    catalyst: 'Draft internal communications, address AI anxiety, or plan engagement campaigns. Share audience context for tailored messaging.',
                    scholar: 'Design training programs, plan champion enablement, or create learning paths. Specify skill levels and objectives for customized plans.',
                    echo: 'Analyze brand voice samples, create style guides, or review AI-generated content for brand alignment. Provide examples of existing content.',
                    nexus: 'Map system dependencies, explore feedback loops, or identify leverage points. Describe the interconnected elements for systems analysis.',
                    coordinator: 'Use Auto mode to have Coordinator route your query to the best specialist agent, or explicitly request multi-agent collaboration on complex topics.',
                  };
                  return howTo[agent.name.toLowerCase()] || 'Interact with this agent through chat or include it in meeting room discussions for specialized insights.';
                })()}
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card p-6">
            <h3 className="text-md font-semibold text-primary mb-4">Agent Activity</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-page rounded-lg text-center">
                <div className="text-2xl font-bold text-primary">{stats.instruction_versions_count}</div>
                <div className="text-xs text-secondary mt-1">Instruction Versions</div>
              </div>
              <div className="p-4 bg-page rounded-lg text-center">
                <div className="text-2xl font-bold text-primary">{stats.kb_documents_count || kb_documents.length}</div>
                <div className="text-xs text-secondary mt-1">KB Documents</div>
              </div>
              <div className="p-4 bg-page rounded-lg text-center">
                <div className="text-2xl font-bold text-primary">{stats.conversations_count}</div>
                <div className="text-xs text-secondary mt-1">Conversations</div>
              </div>
              <div className="p-4 bg-page rounded-lg text-center">
                <div className="text-2xl font-bold text-primary">
                  {agent.is_active ? 'Yes' : 'No'}
                </div>
                <div className="text-xs text-secondary mt-1">Active Status</div>
              </div>
            </div>
          </div>

          {/* Persona Alignment (if applicable) */}
          {(() => {
            const personas: Record<string, { name: string; role: string }> = {
              atlas: { name: 'Chris Baumgartner', role: 'Research & Analytics' },
              fortuna: { name: 'Raul Rivera III', role: 'Finance & Compliance' },
              guardian: { name: 'Danny Leal', role: 'IT & Governance' },
              counselor: { name: 'Ashley Adams', role: 'Legal & Risk' },
              sage: { name: 'Chad Meek', role: 'People & Change' },
              oracle: { name: 'CIPHER v2.1', role: 'Meeting Intelligence' },
            };
            const persona = personas[agent.name.toLowerCase()];
            if (!persona) return null;
            return (
              <div className="card p-6 border-l-4 border-l-blue-500">
                <h3 className="text-md font-semibold text-primary mb-2">Persona Alignment</h3>
                <p className="text-secondary text-sm">
                  This agent&apos;s behavior is modeled after <span className="text-primary font-medium">{persona.name}</span>,
                  representing the <span className="text-primary font-medium">{persona.role}</span> stakeholder perspective.
                </p>
              </div>
            );
          })()}
        </div>
      )}

      {activeTab === 'instructions' && (
        <div className="space-y-6">
          {/* XML File Status Banner */}
          {hasXmlFile && (
            <div className="card p-3 bg-blue-500/10 border-blue-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-blue-400" />
                  <div>
                    <p className="text-sm text-blue-400">
                      <span className="font-medium">{agent.name}.xml</span>
                      {xmlModifiedAt && <span className="text-blue-300/70"> - modified {formatDate(xmlModifiedAt)}</span>}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleSyncFromXml}
                  disabled={syncing}
                  className="px-3 py-1.5 text-xs font-medium text-blue-400 hover:text-blue-300 border border-blue-500/30 rounded-lg hover:border-blue-500/50 transition-colors disabled:opacity-50"
                  title="Reload instructions from the XML file (if you edited it externally)"
                >
                  {syncing ? 'Loading...' : 'Reload from XML'}
                </button>
              </div>
            </div>
          )}

          {/* Current Instructions */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-primary">System Instructions</h2>
              <div className="flex items-center gap-3">
                {active_instruction_version && (
                  <span className="text-sm text-secondary">
                    Version {active_instruction_version.version_number}
                  </span>
                )}
                {!active_instruction_version && hasXmlFile && (
                  <span className="text-sm text-blue-400">
                    From XML file
                  </span>
                )}
              </div>
            </div>

            {editingInstructions ? (
              <div className="space-y-4">
                {/* Edit Mode Toggle */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditMode('text')}
                    className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      editMode === 'text'
                        ? 'bg-primary/20 text-primary border border-primary/30'
                        : 'bg-page text-secondary border border-border hover:border-primary/30'
                    }`}
                  >
                    Edit Text
                  </button>
                  <button
                    onClick={() => setEditMode('upload')}
                    className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      editMode === 'upload'
                        ? 'bg-primary/20 text-primary border border-primary/30'
                        : 'bg-page text-secondary border border-border hover:border-primary/30'
                    }`}
                  >
                    Upload File
                  </button>
                </div>

                {editMode === 'upload' ? (
                  <div className="space-y-4">
                    {/* Hidden file input */}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.xml"
                      onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                      className="hidden"
                    />

                    {/* Drop zone */}
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                        isDragging
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <Upload className="w-8 h-8 mx-auto mb-3 text-secondary" />
                      <p className="text-primary font-medium">
                        Drop your file here or click to browse
                      </p>
                      <p className="text-sm text-secondary mt-1">
                        Accepts .txt or .xml files
                      </p>
                    </div>

                    {/* Uploaded file info */}
                    {uploadedFile && (
                      <div className="bg-page border border-border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-primary" />
                            <div>
                              <p className="font-medium text-primary">{uploadedFile.name}</p>
                              <p className="text-xs text-secondary">{formatFileSize(uploadedFile.size)}</p>
                            </div>
                          </div>
                          <button
                            onClick={clearUploadedFile}
                            className="p-1.5 text-secondary hover:text-red-400 transition-colors"
                            title="Remove file"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                        <div className="border-t border-border pt-3">
                          <p className="text-xs text-secondary uppercase mb-2">Preview</p>
                          <pre className="text-sm text-secondary font-mono max-h-32 overflow-auto whitespace-pre-wrap">
                            {uploadedFile.content.substring(0, 500)}
                            {uploadedFile.content.length > 500 && '...'}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <textarea
                    value={newInstructions}
                    onChange={(e) => setNewInstructions(e.target.value)}
                    className="w-full h-96 px-4 py-3 bg-page border border-border rounded-lg text-primary font-mono text-sm resize-y focus:outline-none focus:border-primary"
                    placeholder="Enter system instructions..."
                  />
                )}

                <input
                  type="text"
                  value={versionDescription}
                  onChange={(e) => setVersionDescription(e.target.value)}
                  placeholder="Version description (optional)"
                  className="w-full px-4 py-2 bg-page border border-border rounded-lg text-primary text-sm focus:outline-none focus:border-primary"
                />
                <div className="flex gap-3">
                  <button
                    onClick={handleDeployInstructions}
                    disabled={saving || !newInstructions.trim()}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? 'Deploying...' : 'Deploy Instructions'}
                  </button>
                  <button
                    onClick={() => {
                      setEditingInstructions(false);
                      setEditMode('text');
                      setUploadedFile(null);
                      // Reset to best available instructions
                      const dbInstructions = active_instruction_version?.instructions || agent.system_instruction || '';
                      const hasValidDb = !isPlaceholderInstruction(dbInstructions);
                      setNewInstructions(hasValidDb ? dbInstructions : (xmlInstructions || ''));
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div>
                {(() => {
                  // Determine what to display: DB version, XML file, or empty message
                  const dbInstructions = active_instruction_version?.instructions || agent.system_instruction;
                  const hasValidDb = !isPlaceholderInstruction(dbInstructions);
                  const displayContent = hasValidDb ? dbInstructions : (xmlInstructions || 'No instructions configured');
                  const isFromXml = !hasValidDb && xmlInstructions;

                  return (
                    <>
                      {isFromXml && (
                        <div className="mb-3 p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                          <p className="text-xs text-blue-400">
                            Showing instructions from XML file. Click &quot;Sync from XML&quot; above to create a versioned copy.
                          </p>
                        </div>
                      )}
                      <pre className="bg-page p-4 rounded-lg text-sm text-secondary overflow-auto max-h-96 whitespace-pre-wrap font-mono">
                        {displayContent}
                      </pre>
                    </>
                  );
                })()}
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
                          {formatDate(version.created_at)}
                        </span>
                        <button
                          onClick={() => handleViewVersion(version.id)}
                          className="px-3 py-1.5 text-xs font-medium text-secondary hover:text-primary border border-border rounded-lg hover:border-primary transition-colors"
                        >
                          View
                        </button>
                        {!version.is_active && (
                          <>
                            <button
                              onClick={() => handleActivateVersion(version.id)}
                              className="px-3 py-1.5 text-xs font-medium text-green-400 hover:text-green-300 border border-green-500/30 rounded-lg hover:border-green-500/50 transition-colors"
                            >
                              Activate
                            </button>
                            <button
                              onClick={() => handleDeleteVersion(version)}
                              disabled={deleting === version.id}
                              className="px-3 py-1.5 text-xs font-medium text-red-400 hover:text-red-300 border border-red-500/30 rounded-lg hover:border-red-500/50 transition-colors disabled:opacity-50"
                            >
                              {deleting === version.id ? 'Deleting...' : 'Delete'}
                            </button>
                          </>
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

      {/* Compare Tab */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          {/* Version Selection */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-primary mb-4">Compare Versions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-sm font-medium text-secondary mb-1">
                  Version A (Older)
                </label>
                <select
                  value={compareVersionA}
                  onChange={(e) => setCompareVersionA(e.target.value)}
                  className="w-full px-4 py-2 bg-page border border-border rounded-lg text-primary text-sm focus:outline-none focus:border-primary"
                >
                  <option value="">Select version...</option>
                  {instruction_versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.version_number} {v.is_active ? '(Active)' : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-secondary mb-1">
                  Version B (Newer)
                </label>
                <select
                  value={compareVersionB}
                  onChange={(e) => setCompareVersionB(e.target.value)}
                  className="w-full px-4 py-2 bg-page border border-border rounded-lg text-primary text-sm focus:outline-none focus:border-primary"
                >
                  <option value="">Select version...</option>
                  {instruction_versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.version_number} {v.is_active ? '(Active)' : ''}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleCompare}
                disabled={!compareVersionA || !compareVersionB || comparing}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {comparing ? (
                  <span className="flex items-center justify-center gap-2">
                    <LoadingSpinner size="sm" />
                    Comparing...
                  </span>
                ) : (
                  'Generate Comparison'
                )}
              </button>
            </div>
          </div>

          {/* Comparison Stats */}
          {compareResult && (
            <div className="card p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-secondary">
                    Comparing <span className="font-medium text-primary">{compareResult.version_a.version_number}</span>
                    {' → '}
                    <span className="font-medium text-primary">{compareResult.version_b.version_number}</span>
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-green-400">+{compareResult.stats.additions} additions</span>
                  <span className="text-red-400">-{compareResult.stats.deletions} deletions</span>
                  <span className="text-secondary">({compareResult.stats.total_changes} total changes)</span>
                </div>
              </div>
            </div>
          )}

          {/* AI Summary */}
          {compareResult && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-primary">AI Summary</h3>
                {!summaryResult && (
                  <button
                    onClick={handleGenerateSummary}
                    disabled={generatingSummary}
                    className="px-4 py-2 text-sm font-medium text-blue-400 hover:text-blue-300 border border-blue-500/30 rounded-lg hover:border-blue-500/50 transition-colors disabled:opacity-50"
                  >
                    {generatingSummary ? (
                      <span className="flex items-center gap-2">
                        <LoadingSpinner size="sm" />
                        Generating...
                      </span>
                    ) : (
                      'Generate AI Summary'
                    )}
                  </button>
                )}
              </div>
              {summaryResult ? (
                <div className="prose prose-invert max-w-none">
                  <div className="text-secondary whitespace-pre-wrap">{summaryResult.summary}</div>
                </div>
              ) : generatingSummary ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="lg" />
                  <span className="ml-3 text-secondary">Analyzing changes with Claude...</span>
                </div>
              ) : (
                <div className="text-center py-8 text-secondary">
                  <p>Click &quot;Generate AI Summary&quot; to get a natural language analysis of the changes.</p>
                  <p className="text-sm mt-2 text-muted">This uses Claude to analyze the diff and provide actionable insights.</p>
                </div>
              )}
            </div>
          )}

          {/* Line-by-Line Diff */}
          {compareResult && (
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-primary mb-4">Line-by-Line Diff</h3>
              <div className="max-h-[500px] overflow-y-auto rounded-lg bg-page border border-border p-4">
                <pre className="text-sm font-mono whitespace-pre-wrap">
                  {compareResult.diff.map((line, index) => {
                    let className = 'text-secondary';
                    if (line.startsWith('+') && !line.startsWith('+++')) {
                      className = 'text-green-400 bg-green-500/10';
                    } else if (line.startsWith('-') && !line.startsWith('---')) {
                      className = 'text-red-400 bg-red-500/10';
                    } else if (line.startsWith('@@')) {
                      className = 'text-blue-400';
                    }
                    return (
                      <div key={index} className={className}>
                        {line}
                      </div>
                    );
                  })}
                </pre>
              </div>
            </div>
          )}

          {!compareResult && !comparing && (
            <div className="card p-12 text-center">
              <p className="text-secondary">Select two versions above and click &quot;Generate Comparison&quot; to see a detailed diff.</p>
            </div>
          )}
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

      {/* View Version Modal */}
      {viewingVersion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-card rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-border">
            {/* Header */}
            <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-primary">Version {viewingVersion.version_number}</h2>
                <p className="text-sm text-secondary">Created {formatDate(viewingVersion.created_at)}</p>
              </div>
              <button
                onClick={() => setViewingVersion(null)}
                className="text-secondary hover:text-primary transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {/* Metadata */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 rounded-lg bg-page">
                  <p className="text-xs text-secondary uppercase">Status</p>
                  <p className="font-medium text-primary">
                    {viewingVersion.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-page">
                  <p className="text-xs text-secondary uppercase">Characters</p>
                  <p className="font-medium text-primary">{viewingVersion.instructions.length.toLocaleString()}</p>
                </div>
                <div className="p-3 rounded-lg bg-page">
                  <p className="text-xs text-secondary uppercase">Words</p>
                  <p className="font-medium text-primary">{viewingVersion.instructions.split(/\s+/).filter(Boolean).length.toLocaleString()}</p>
                </div>
                {viewingVersion.activated_at && (
                  <div className="p-3 rounded-lg bg-page">
                    <p className="text-xs text-secondary uppercase">Activated</p>
                    <p className="font-medium text-primary">{formatDate(viewingVersion.activated_at)}</p>
                  </div>
                )}
              </div>

              {/* Description */}
              {viewingVersion.description && (
                <div>
                  <h3 className="text-sm font-medium text-secondary uppercase mb-2">Version Notes</h3>
                  <p className="text-primary">{viewingVersion.description}</p>
                </div>
              )}

              {/* Content */}
              <div>
                <h3 className="text-sm font-medium text-secondary uppercase mb-2">Full Content</h3>
                <div className="max-h-96 overflow-y-auto rounded-lg bg-page border border-border p-4">
                  <pre className="text-sm text-secondary whitespace-pre-wrap font-mono">
                    {viewingVersion.instructions}
                  </pre>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-page px-6 py-4 border-t border-border flex gap-3">
              {!viewingVersion.is_active && (
                <button
                  onClick={() => {
                    handleActivateVersion(viewingVersion.id);
                    setViewingVersion(null);
                  }}
                  className="btn-primary"
                >
                  Activate This Version
                </button>
              )}
              <button
                onClick={() => setViewingVersion(null)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
