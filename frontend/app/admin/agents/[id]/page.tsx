'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { Upload, FileText, X, ArrowLeft, Check, Diamond, ChevronRight, Circle, FileBarChart, Loader2, ListChecks } from 'lucide-react';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from '@/components/LoadingSpinner';
import { AgentIcon, getAgentColor } from '@/components/AgentIcon';
import CareerStatusReportModal from '@/components/compass/CareerStatusReportModal';
import TaskCandidateReviewModal from '@/components/tasks/TaskCandidateReviewModal';

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

  // Compass career status report state
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [careerReport, setCareerReport] = useState<any>(null);
  const [careerReportLoading, setCareerReportLoading] = useState(false);
  const [showCareerReportModal, setShowCareerReportModal] = useState(false);

  // Taskmaster task scanning state
  interface TaskCandidate {
    id: string;
    title: string;
    source_document_name: string;
    suggested_priority: number;
    due_date_text?: string;
    confidence: string;
  }
  interface ScanApiResponse {
    success: boolean;
    documents_scanned: number;
    total_tasks_found: number;
    total_tasks_stored: number;
    message: string;
  }
  interface ScanResult {
    documents_scanned: number;
    total_candidates_found: number;
    candidates: TaskCandidate[];
  }
  const [taskScanResult, setTaskScanResult] = useState<ScanResult | null>(null);
  const [taskScanLoading, setTaskScanLoading] = useState(false);
  const [showCandidateReview, setShowCandidateReview] = useState(false);

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

  // Generate career status report for Compass agent
  const handleGenerateCareerReport = async () => {
    try {
      setCareerReportLoading(true);
      const report = await apiPost('/api/compass/status-report/generate', {});
      setCareerReport(report);
      setShowCareerReportModal(true);
    } catch (err) {
      logger.error('Failed to generate career report:', err);
      toast.error('Failed to generate career status report');
    } finally {
      setCareerReportLoading(false);
    }
  };

  // Scan documents for tasks (Taskmaster agent)
  const handleScanDocumentsForTasks = async () => {
    try {
      setTaskScanLoading(true);
      setTaskScanResult(null);

      // First, trigger the scan
      const scanResponse = await apiPost<ScanApiResponse>('/api/tasks/scan-documents?limit=10&since_days=30', {});

      // Then fetch the pending candidates to display
      const candidatesResponse = await apiGet<{ candidates: TaskCandidate[] }>('/api/tasks/candidates?status=pending&limit=20');

      const result: ScanResult = {
        documents_scanned: scanResponse.documents_scanned,
        total_candidates_found: candidatesResponse.candidates?.length || 0,
        candidates: candidatesResponse.candidates || []
      };

      setTaskScanResult(result);

      if (result.candidates.length > 0) {
        // Open the review modal to process candidates
        setShowCandidateReview(true);
      } else {
        toast.success(`Scanned ${scanResponse.documents_scanned} documents - no pending tasks to review`);
      }
    } catch (err) {
      logger.error('Failed to scan documents for tasks:', err);
      toast.error('Failed to scan documents for tasks');
    } finally {
      setTaskScanLoading(false);
    }
  };

  const handleCandidateReviewComplete = (stats: { accepted: number; rejected: number }) => {
    setShowCandidateReview(false);
    setTaskScanResult(null);
    if (stats.accepted > 0 || stats.rejected > 0) {
      toast.success(`Review complete: ${stats.accepted} task(s) created, ${stats.rejected} skipped`);
    }
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
        className="inline-flex items-center gap-2 text-secondary hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>All Agents</span>
      </Link>

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
        <div className="space-y-4">
          {/* Panel 1: What This Agent Does - Open by default */}
          <details open className="card group">
            <summary className="cursor-pointer p-4 flex items-center justify-between hover:bg-page/50 transition-colors rounded-t-lg">
              <h2 className="text-lg font-semibold text-primary">What This Agent Does</h2>
              <svg className="w-5 h-5 text-secondary transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="px-6 pb-6 pt-2 border-t border-border">
              {(() => {
                const agentOverviews: Record<string, {
                  summary: string;
                  keyActions: string[];
                  persona?: string;
                }> = {
                  atlas: {
                    summary: 'Research intelligence agent specializing in GenAI implementation. Atlas performs live web searches with credibility-tiered source filtering, synthesizes knowledge base documents, and applies Lean methodology to deliver actionable insights backed by consulting firms, Big 4, and industry publications.',
                    keyActions: [
                      'Searches web with 4-tier credibility filtering (consulting firms, Big 4/tech, industry pubs, blogs)',
                      'Synthesizes research from knowledge base with RAG retrieval',
                      'Provides industry benchmarks and competitive analysis',
                      'Applies Lean methodology to prioritize actionable over theoretical insights'
                    ],
                    persona: 'Chris Baumgartner'
                  },
                  capital: {
                    summary: 'Financial analysis agent for AI investment justification. Capital builds defensible business cases, calculates ROI projections, identifies hidden costs, and ensures SOX compliance. Bridges the gap between AI potential and financial reality with CFO-ready analysis.',
                    keyActions: [
                      'Builds business cases with ROI frameworks and TCO calculations',
                      'Identifies hidden costs beyond licensing fees',
                      'Provides risk-adjusted financial projections',
                      'Ensures SOX and financial regulatory alignment'
                    ],
                    persona: 'Raul Rivera III'
                  },
                  guardian: {
                    summary: 'IT governance and security agent for enterprise AI deployments. Guardian evaluates vendor security posture, detects shadow AI usage, maps implementations to compliance frameworks, and designs unified AI governance policies that enable innovation while maintaining protection.',
                    keyActions: [
                      'Evaluates AI vendors against security frameworks (SOC 2, GDPR, etc.)',
                      'Detects and manages unauthorized shadow AI usage',
                      'Designs AI governance policies and steering structures',
                      'Maps AI implementations to regulatory requirements'
                    ],
                    persona: 'Danny Leal'
                  },
                  counselor: {
                    summary: 'Legal guidance agent for AI contracts, compliance, and risk. Counselor reviews vendor terms for red flags, clarifies IP ownership questions, navigates data privacy regulations, and provides practical legal guidance that enables AI adoption without undue exposure.',
                    keyActions: [
                      'Reviews AI vendor contracts for problematic terms',
                      'Clarifies IP ownership for fine-tuned models and AI outputs',
                      'Navigates GDPR, CCPA, and evolving AI legislation',
                      'Assesses liability exposure for AI-generated content'
                    ],
                    persona: 'Ashley Adams'
                  },
                  oracle: {
                    summary: 'Meeting intelligence agent that transforms recordings into strategic insights. Oracle parses transcripts to extract stakeholder positions with evidence-based sentiment, maps power dynamics and influence patterns, and surfaces key decisions and action items.',
                    keyActions: [
                      'Extracts stakeholder positions with supporting quotes',
                      'Maps power dynamics and influence relationships',
                      'Identifies decision-makers and their concerns',
                      'Synthesizes action items and ownership from discussions'
                    ],
                    persona: 'CIPHER v2.1'
                  },
                  sage: {
                    summary: 'People and change management agent focused on human flourishing. Sage diagnoses adoption challenges using incentive analysis (Buffett principle), designs champion programs that prevent burnout, addresses AI anxiety with empathy, and ensures AI augments rather than replaces human judgment.',
                    keyActions: [
                      'Diagnoses adoption stalls through incentive and motivation analysis',
                      'Designs sustainable champion programs and peer networks',
                      'Addresses employee fear and AI anxiety with transparency',
                      'Evaluates implementations for human sovereignty preservation'
                    ],
                    persona: 'Chad Meek'
                  },
                  strategist: {
                    summary: 'Executive strategy agent for C-suite engagement and organizational alignment. Strategist builds sponsorship coalitions, navigates political landscapes, designs governance frameworks, and crafts board-ready communications that align AI initiatives with executive priorities.',
                    keyActions: [
                      'Builds executive sponsorship and coalition support',
                      'Navigates organizational politics and stakeholder dynamics',
                      'Designs AI steering committees and governance structures',
                      'Crafts board presentations and executive communications'
                    ]
                  },
                  architect: {
                    summary: 'Technical architecture agent for enterprise AI system design. Architect designs coherent AI patterns including RAG implementations, plans system integrations, provides build-vs-buy frameworks, and ensures scalability while balancing innovation with enterprise stability.',
                    keyActions: [
                      'Designs enterprise AI architecture patterns',
                      'Plans RAG implementations and system integrations',
                      'Provides frameworks for build-vs-buy technology decisions',
                      'Anticipates scalability and growth requirements'
                    ]
                  },
                  operator: {
                    summary: 'Business operations agent for process optimization and automation. Operator identifies automation opportunities, defines meaningful KPIs for AI initiatives, maps workflows to find bottlenecks, and establishes baselines for measuring improvement.',
                    keyActions: [
                      'Identifies high-value automation opportunities',
                      'Defines KPIs and metrics for AI initiatives',
                      'Maps workflows and identifies efficiency bottlenecks',
                      'Establishes baselines for measuring AI impact'
                    ]
                  },
                  pioneer: {
                    summary: 'Innovation and emerging technology agent that separates signal from noise. Pioneer scouts new AI capabilities, assesses technology maturity for enterprise readiness, filters hype from practical value, and scopes proof-of-concept experiments.',
                    keyActions: [
                      'Scouts emerging AI capabilities and trends',
                      'Assesses technology maturity using hype cycle positioning',
                      'Filters marketing hype from practical enterprise value',
                      'Scopes proof-of-concept experiments for new technologies'
                    ]
                  },
                  catalyst: {
                    summary: 'Internal communications agent for AI messaging and employee engagement. Catalyst drafts launch announcements, creates FAQs addressing common concerns, designs engagement campaigns, and builds trust through transparent communication about AI initiatives.',
                    keyActions: [
                      'Drafts all-hands announcements and town hall talking points',
                      'Creates FAQs addressing employee AI concerns',
                      'Designs engagement campaigns for AI adoption',
                      'Develops narratives that build trust and enthusiasm'
                    ]
                  },
                  scholar: {
                    summary: 'Learning and development agent applying adult learning principles to AI skill building. Scholar designs role-based training curricula, creates champion enablement programs, builds peer learning communities, and measures training effectiveness.',
                    keyActions: [
                      'Designs AI literacy curricula for different skill levels',
                      'Creates learning paths for AI champions',
                      'Builds peer learning and knowledge-sharing structures',
                      'Measures and reinforces training effectiveness'
                    ]
                  },
                  echo: {
                    summary: 'Brand voice agent ensuring AI-generated content maintains authenticity. Echo analyzes writing samples to define voice, creates AI writing guidelines aligned with brand identity, reviews content for consistency, and balances AI efficiency with human authenticity.',
                    keyActions: [
                      'Analyzes writing samples to define brand voice attributes',
                      'Creates AI writing guidelines for content generation',
                      'Reviews AI-generated content for brand alignment',
                      'Develops persona guidelines for multi-channel consistency'
                    ]
                  },
                  nexus: {
                    summary: 'Systems thinking agent that reveals hidden connections and consequences. Nexus maps dependencies between AI initiatives, identifies feedback loops and leverage points, models ripple effects of decisions, and catches blind spots that siloed thinking misses.',
                    keyActions: [
                      'Maps dependencies and interconnections between initiatives',
                      'Identifies feedback loops and high-impact leverage points',
                      'Models unintended consequences and ripple effects',
                      'Challenges consensus to surface hidden assumptions'
                    ]
                  },
                  coordinator: {
                    summary: 'Central orchestration agent for multi-agent collaboration in chat. Coordinator routes queries to the best specialist, synthesizes perspectives from multiple agents, maintains conversation coherence, and makes the full agent roster accessible without requiring user expertise.',
                    keyActions: [
                      'Routes queries to the most relevant specialist agent',
                      'Synthesizes multi-agent perspectives into coherent responses',
                      'Maintains context across agent handoffs',
                      'Identifies when multiple agents should collaborate'
                    ]
                  },
                  facilitator: {
                    summary: 'Meeting orchestration meta-agent that makes other agents brilliant. Facilitator welcomes participants, clarifies user intent before opening discussion, routes topics to relevant specialists, enforces balanced participation, and ensures systems thinking is invoked before conclusions are reached.',
                    keyActions: [
                      'Welcomes users and clarifies intent before inviting specialists',
                      'Routes topics to relevant agents with brief context',
                      'Enforces balanced participation - no single agent dominates',
                      'Invokes systems thinking before conclusions are reached'
                    ]
                  },
                  reporter: {
                    summary: 'Meeting synthesis meta-agent that distills multi-agent discussions into unified documentation. Reporter creates summaries with proper attribution to source agents, extracts action items with ownership, produces executive briefs ready for stakeholder sharing, and preserves disagreements rather than forcing false consensus.',
                    keyActions: [
                      'Synthesizes multi-agent discussions into coherent summaries',
                      'Attributes insights to source agents for transparency',
                      'Extracts action items with owners and dependencies',
                      'Produces executive briefs suitable for direct stakeholder sharing'
                    ]
                  },
                  compass: {
                    summary: 'Personal career development coach that helps professionals track performance through conversation, not forms. Compass captures wins with impact metrics, prepares you for manager check-ins with concrete evidence, tracks goals against company strategic priorities, and builds a running narrative of your professional growth.',
                    keyActions: [
                      'Captures wins conversationally and asks smart follow-ups for impact metrics',
                      'Prepares check-in talking points by synthesizing recent wins and goal progress',
                      'Validates work against company strategic priorities and FY goals',
                      'Generates reflection prompts and surfaces patterns in your growth'
                    ]
                  },
                  taskmaster: {
                    summary: 'Personal accountability partner that surfaces tasks from meetings and documents, tracks progress, and keeps you focused on the right work. Taskmaster captures commitments conversationally, detects slippage before it becomes a crisis, and provides prioritized focus guidance.',
                    keyActions: [
                      'Scans KB documents and transcripts for your task commitments',
                      'Extracts explicit and inferred tasks with source attribution',
                      'Groups tasks by urgency: overdue, today, this week, blocked',
                      'Provides focus guidance based on priority and deadlines'
                    ]
                  }
                };
                const overview = agentOverviews[agent.name.toLowerCase()];
                if (!overview) {
                  return (
                    <p className="text-secondary leading-relaxed">
                      {agent.description || 'No description configured for this agent.'}
                    </p>
                  );
                }

                return (
                  <div className="space-y-4">
                    <p className="text-secondary leading-relaxed">
                      {overview.summary}
                    </p>
                    <div>
                      <h4 className="text-sm font-semibold text-primary mb-2">Key Actions</h4>
                      <ul className="space-y-1.5">
                        {overview.keyActions.map((action, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                            <Circle className="w-1.5 h-1.5 text-primary mt-2 flex-shrink-0 fill-current" />
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                );
              })()}
            </div>
          </details>

          {/* Compass-specific: Career Status Report Panel */}
          {agent.name.toLowerCase() === 'compass' && (
            <details open className="card group">
              <summary className="cursor-pointer p-4 flex items-center justify-between hover:bg-page/50 transition-colors rounded-t-lg">
                <h2 className="text-lg font-semibold text-primary flex items-center gap-2">
                  <FileBarChart className="w-5 h-5 text-amber-500" />
                  Career Status Report
                </h2>
                <svg className="w-5 h-5 text-secondary transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="px-6 pb-6 pt-2 border-t border-border">
                <p className="text-secondary text-sm mb-4">
                  Generate a comprehensive career status report based on your Knowledge Base documents.
                  The report assesses your performance across 5 dimensions: Strategic Impact, Execution Quality,
                  Relationship Building, Growth Mindset, and Leadership Presence.
                </p>
                <button
                  onClick={handleGenerateCareerReport}
                  disabled={careerReportLoading}
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium"
                >
                  {careerReportLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating Report...
                    </>
                  ) : (
                    <>
                      <FileBarChart className="w-5 h-5" />
                      Generate Career Status Report
                    </>
                  )}
                </button>
                <p className="text-muted text-xs mt-3">
                  For best results, upload career-related documents (performance reviews, goals, win logs) to the Knowledge Base and tag them for Compass.
                </p>
              </div>
            </details>
          )}

          {/* Taskmaster-specific: Scan Documents Panel */}
          {agent.name.toLowerCase() === 'taskmaster' && (
            <details open className="card group">
              <summary className="cursor-pointer p-4 flex items-center justify-between hover:bg-page/50 transition-colors rounded-t-lg">
                <h2 className="text-lg font-semibold text-primary flex items-center gap-2">
                  <ListChecks className="w-5 h-5 text-amber-500" />
                  Task Discovery
                </h2>
                <svg className="w-5 h-5 text-secondary transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="px-6 pb-6 pt-2 border-t border-border">
                <p className="text-secondary text-sm mb-4">
                  Scan your recent Knowledge Base documents (meetings, transcripts, notes) for potential tasks.
                  Found tasks are saved as candidates for you to review, accept, or reject.
                </p>
                <button
                  onClick={handleScanDocumentsForTasks}
                  disabled={taskScanLoading}
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors disabled:opacity-50 font-medium"
                >
                  {taskScanLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Scanning Documents...
                    </>
                  ) : (
                    <>
                      <ListChecks className="w-5 h-5" />
                      Scan Recent Documents
                    </>
                  )}
                </button>

                {/* Show button to review pending candidates if any exist */}
                {taskScanResult && taskScanResult.candidates.length > 0 && !showCandidateReview && (
                  <button
                    onClick={() => setShowCandidateReview(true)}
                    className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-page border border-amber-500/30 text-amber-400 rounded-lg hover:bg-amber-500/10 transition-colors"
                  >
                    <ListChecks className="w-5 h-5" />
                    Review {taskScanResult.candidates.length} Pending Task{taskScanResult.candidates.length !== 1 ? 's' : ''}
                  </button>
                )}

                <p className="text-muted text-xs mt-3">
                  Scans documents from the last 30 days. Tasks are extracted from commitments like &quot;I will...&quot;, &quot;I&apos;ll follow up...&quot;, or explicit action items.
                </p>
              </div>
            </details>
          )}

          {/* Panel 2: Why It Exists - Collapsed by default */}
          <details className="card group">
            <summary className="cursor-pointer p-4 flex items-center justify-between hover:bg-page/50 transition-colors rounded-t-lg">
              <h2 className="text-lg font-semibold text-primary">Why It Exists</h2>
              <svg className="w-5 h-5 text-secondary transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="px-6 pb-6 pt-2 border-t border-border">
              {(() => {
                const agentDetails: Record<string, {
                  purpose: string;
                  problemsSolved: string[];
                  uniqueValue: string;
                  keyPrinciples?: string[];
                }> = {
                  atlas: {
                    purpose: 'Research intelligence for GenAI implementation using Lean methodology and competitive benchmarking.',
                    problemsSolved: [
                      'Information overload - filters signal from noise in AI research',
                      'Credibility gaps - uses tiered source filtering (Tier 1: consulting firms, Tier 2: Big 4/tech, Tier 3: industry pubs)',
                      'Knowledge silos - synthesizes insights from multiple sources with citations',
                      'Outdated recommendations - performs live web search for current data'
                    ],
                    uniqueValue: 'Combines web search with knowledge base RAG, applying Lean methodology to prioritize actionable over theoretical insights.'
                  },
                  capital: {
                    purpose: 'Financial analysis including ROI, business cases, and SOX compliance for AI investments.',
                    problemsSolved: [
                      'Justification hurdles - builds compelling business cases for AI investment',
                      'Hidden costs - identifies total cost of ownership beyond licensing fees',
                      'Compliance risk - ensures SOX and financial regulatory alignment',
                      'Stakeholder skepticism - provides CFO-ready financial projections'
                    ],
                    uniqueValue: 'Bridges the gap between AI potential and financial reality with defensible projections and risk-adjusted returns.'
                  },
                  guardian: {
                    purpose: 'IT governance, security compliance, shadow IT detection, and vendor evaluation.',
                    problemsSolved: [
                      'Shadow AI proliferation - detects unauthorized AI tool usage',
                      'Vendor risk - evaluates AI providers against security frameworks',
                      'Compliance gaps - maps AI implementations to regulatory requirements',
                      'Governance fragmentation - creates unified AI governance policies'
                    ],
                    uniqueValue: 'Proactive security posture that enables innovation while maintaining enterprise-grade protection and compliance.'
                  },
                  counselor: {
                    purpose: 'Legal considerations: contracts, AI risk, liability, and data privacy.',
                    problemsSolved: [
                      'Contract blind spots - identifies risky AI vendor terms',
                      'Liability exposure - clarifies AI-generated content ownership',
                      'Privacy violations - ensures GDPR, CCPA, and data protection compliance',
                      'Regulatory uncertainty - navigates evolving AI legislation'
                    ],
                    uniqueValue: 'Practical legal guidance that enables AI adoption without exposing the organization to undue legal risk.'
                  },
                  oracle: {
                    purpose: 'Meeting transcript analysis for stakeholder insights and sentiment with evidence.',
                    problemsSolved: [
                      'Lost meeting insights - extracts key decisions and action items',
                      'Stakeholder blindness - maps positions, concerns, and influence',
                      'Sentiment ambiguity - provides evidence-based sentiment with quotes',
                      'Power dynamics opacity - reveals who influences whom'
                    ],
                    uniqueValue: 'Transforms meeting recordings into strategic intelligence with evidence-backed stakeholder analysis.'
                  },
                  sage: {
                    purpose: 'Change management, human flourishing, incentive analysis, and human-centered AI adoption.',
                    problemsSolved: [
                      'Adoption resistance - addresses fear and skepticism with empathy',
                      'Champion burnout - designs sustainable support structures',
                      'Misaligned incentives - diagnoses why adoption stalls using Buffett principle',
                      'Human sovereignty erosion - ensures AI augments rather than replaces human judgment'
                    ],
                    uniqueValue: 'People-first approach that treats adoption as a community problem, not a technology problem.',
                    keyPrinciples: [
                      'Incentives Drive Outcomes: "Show me the incentive and I\'ll show you the outcome" (Buffett)',
                      'Human Sovereignty: AI recommends, humans decide - always',
                      'Augmentation Over Automation: Focus on tedious tasks, preserve meaningful work',
                      'Fear Is Rational: 1/3 of employees may fear job loss - address honestly'
                    ]
                  },
                  strategist: {
                    purpose: 'C-suite engagement, organizational politics, and governance design.',
                    problemsSolved: [
                      'Executive misalignment - builds sponsorship and coalition',
                      'Political landmines - navigates organizational dynamics',
                      'Governance gaps - designs AI steering committees and policies',
                      'Communication failures - crafts board-ready messaging'
                    ],
                    uniqueValue: 'Strategic perspective that aligns AI initiatives with executive priorities and organizational reality.'
                  },
                  architect: {
                    purpose: 'Technical architecture for enterprise AI: RAG, integrations, build vs. buy.',
                    problemsSolved: [
                      'Architecture sprawl - designs coherent enterprise AI patterns',
                      'Integration complexity - plans system interconnections',
                      'Build vs buy paralysis - provides framework for technology decisions',
                      'Scalability blind spots - anticipates growth requirements'
                    ],
                    uniqueValue: 'Pragmatic architecture guidance balancing innovation with enterprise stability and maintainability.'
                  },
                  operator: {
                    purpose: 'Business process optimization, automation, and operational metrics.',
                    problemsSolved: [
                      'Process inefficiency - identifies automation opportunities',
                      'Metric gaps - defines meaningful KPIs for AI initiatives',
                      'Workflow bottlenecks - maps and optimizes business processes',
                      'ROI invisibility - establishes baselines for measuring improvement'
                    ],
                    uniqueValue: 'Operational lens that grounds AI in measurable business outcomes and sustainable process improvement.'
                  },
                  pioneer: {
                    purpose: 'Emerging technology scouting, hype filtering, and maturity assessment.',
                    problemsSolved: [
                      'Hype overload - separates viable innovation from marketing noise',
                      'Timing risk - assesses technology maturity for enterprise readiness',
                      'Opportunity blindness - scouts emerging capabilities competitors may miss',
                      'POC paralysis - scopes practical proof-of-concept experiments'
                    ],
                    uniqueValue: 'Forward-looking perspective that balances innovation enthusiasm with pragmatic maturity assessment.'
                  },
                  catalyst: {
                    purpose: 'Internal AI communications, employee engagement, and AI anxiety.',
                    problemsSolved: [
                      'Communication void - fills the gap with proactive AI messaging',
                      'AI anxiety - addresses fear and uncertainty with transparent communication',
                      'Engagement gaps - designs campaigns that build AI enthusiasm',
                      'Message fragmentation - creates consistent narrative across channels'
                    ],
                    uniqueValue: 'Human-centered communications that build trust and excitement while honestly addressing concerns.'
                  },
                  scholar: {
                    purpose: 'Training programs, champion enablement, and adult learning principles.',
                    problemsSolved: [
                      'Skill gaps - designs targeted AI upskilling programs',
                      'One-size-fits-all training - creates role-based learning paths',
                      'Champion isolation - builds peer learning communities',
                      'Knowledge decay - designs reinforcement and continuous learning'
                    ],
                    uniqueValue: 'Adult learning expertise applied to AI skill development with sustainable champion enablement.'
                  },
                  echo: {
                    purpose: 'Brand voice analysis, style profiling, and AI content guidelines.',
                    problemsSolved: [
                      'Voice inconsistency - maintains brand identity in AI-generated content',
                      'Style drift - creates guidelines for AI writing alignment',
                      'Authenticity concerns - balances AI efficiency with human voice',
                      'Multi-channel fragmentation - ensures consistent tone everywhere'
                    ],
                    uniqueValue: 'Brand guardian that ensures AI-generated content sounds authentically like your organization.'
                  },
                  nexus: {
                    purpose: 'Systems thinking: interconnections, feedback loops, and leverage points.',
                    problemsSolved: [
                      'Siloed thinking - reveals hidden dependencies between initiatives',
                      'Unintended consequences - models ripple effects of AI decisions',
                      'Leverage blindness - identifies high-impact intervention points',
                      'Complexity paralysis - maps systems into actionable insights'
                    ],
                    uniqueValue: 'Holistic perspective that prevents AI initiatives from creating new problems while solving old ones.'
                  },
                  coordinator: {
                    purpose: 'Multi-agent orchestration, query routing, and response synthesis.',
                    problemsSolved: [
                      'Agent selection confusion - automatically routes to best specialist',
                      'Response fragmentation - synthesizes multi-agent perspectives',
                      'Context loss - maintains conversation coherence across agents',
                      'Expertise gaps - identifies when multiple agents should collaborate'
                    ],
                    uniqueValue: 'Intelligent orchestration that makes the full agent roster accessible without requiring user expertise.'
                  },
                  facilitator: {
                    purpose: 'Meeting orchestration - welcomes users, clarifies intent, routes to specialists, ensures balanced participation.',
                    problemsSolved: [
                      'Meeting chaos - provides structure and flow to multi-agent discussions',
                      'Agent dominance - ensures balanced participation across specialists',
                      'Intent ambiguity - clarifies user goals before diving into discussion',
                      'Premature conclusions - invokes systems thinking before finalizing'
                    ],
                    uniqueValue: 'Meta-agent that makes other agents brilliant - not a domain expert, but a skilled conductor of expertise.'
                  },
                  reporter: {
                    purpose: 'Meeting synthesis and documentation - distills multi-agent discussions into unified summaries, action items, and executive briefs.',
                    problemsSolved: [
                      'Summary confusion - one voice instead of multiple agents each giving their own recap',
                      'Lost attribution - tracks which agent said what for transparency and follow-up',
                      'False consensus - preserves disagreements rather than smoothing over tensions',
                      'Documentation burden - produces shareable executive briefs ready for stakeholders'
                    ],
                    uniqueValue: 'Single source of truth for meeting documentation that respects all voices while creating unified, actionable output.'
                  },
                  compass: {
                    purpose: 'Personal career development through conversational win capture, check-in preparation, and strategic alignment tracking.',
                    problemsSolved: [
                      'Forgotten wins - captures accomplishments before they fade from memory',
                      'Empty check-ins - prepares concrete talking points with evidence',
                      'Strategic disconnect - connects daily work to company priorities',
                      'Review scramble - maintains running record for performance conversations',
                      'Admin burden - extracts structure from conversation, not forms'
                    ],
                    uniqueValue: 'Makes career tracking effortless by treating conversation as data entry - you talk about what you did, Compass captures the impact.',
                    keyPrinciples: [
                      'Growth happens in moments that are easily forgotten - capture them',
                      'Strategic alignment beats task completion',
                      'Your manager is not a mind reader - document with specifics',
                      'Competency without evidence is invisible'
                    ]
                  },
                  taskmaster: {
                    purpose: 'Personal accountability for task commitments made across meetings and documents.',
                    problemsSolved: [
                      'Lost commitments - captures tasks from meetings before they are forgotten',
                      'Slippage blindness - alerts on overdue and at-risk tasks before crisis',
                      'Focus paralysis - prioritizes what to work on based on urgency',
                      'Tracking burden - extracts tasks automatically from documents',
                      'Scattered tasks - consolidates commitments from multiple sources'
                    ],
                    uniqueValue: 'Proactive accountability partner that surfaces your commitments and keeps you focused without tedious manual tracking.',
                    keyPrinciples: [
                      'Commitments made in meetings are easily forgotten without capture',
                      'Proactive reminders prevent slippage better than reactive fire-fighting',
                      'Focus on YOUR tasks, not team project management',
                      'Small daily progress beats heroic catch-up efforts'
                    ]
                  }
                };
                const detail = agentDetails[agent.name.toLowerCase()];
                if (!detail) {
                  return <p className="text-secondary">Specialized capabilities within the Thesis platform.</p>;
                }

                return (
                  <div className="space-y-6">
                    <p className="text-secondary leading-relaxed">{detail.purpose}</p>

                    <div>
                      <h4 className="text-sm font-semibold text-primary mb-3">Problems Solved</h4>
                      <ul className="space-y-2">
                        {detail.problemsSolved.map((problem, i) => (
                          <li key={i} className="flex items-start gap-3 text-sm text-secondary">
                            <Check className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                            {problem}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {detail.keyPrinciples && (
                      <div>
                        <h4 className="text-sm font-semibold text-primary mb-3">Key Principles</h4>
                        <ul className="space-y-2">
                          {detail.keyPrinciples.map((principle, i) => (
                            <li key={i} className="flex items-start gap-3 text-sm text-secondary">
                              <Diamond className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                              {principle}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="pt-4 border-t border-border">
                      <h4 className="text-sm font-semibold text-primary mb-2">Unique Value</h4>
                      <p className="text-secondary text-sm leading-relaxed">{detail.uniqueValue}</p>
                    </div>
                  </div>
                );
              })()}
            </div>
          </details>

          {/* Panel 3: How To Use It - Collapsed by default */}
          <details className="card group">
            <summary className="cursor-pointer p-4 flex items-center justify-between hover:bg-page/50 transition-colors rounded-t-lg">
              <h2 className="text-lg font-semibold text-primary">How To Use It</h2>
              <svg className="w-5 h-5 text-secondary transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="px-6 pb-6 pt-2 border-t border-border">
              {(() => {
                const usageDetails: Record<string, {
                  howToUse: string;
                  capabilities: string[];
                  bestFor: string[];
                  examplePrompts: string[];
                  tips?: string[];
                }> = {
                  atlas: {
                    howToUse: 'Ask research questions about GenAI trends or best practices. Atlas searches web and KB for sourced answers.',
                    capabilities: ['Web search with credibility filtering (Tier 1-4 sources)', 'Knowledge base RAG retrieval', 'Competitive benchmarking', 'Lean methodology application'],
                    bestFor: ['Industry trend analysis', 'Best practice research', 'Vendor comparisons', 'Academic/consulting firm insights'],
                    examplePrompts: [
                      'What are the latest best practices for enterprise RAG implementation?',
                      'How are Fortune 500 companies measuring AI ROI?',
                      'Compare the AI strategies of Microsoft, Google, and Anthropic',
                      'What does McKinsey say about AI adoption barriers?'
                    ],
                    tips: ['Specify the industry context for more relevant results', 'Ask for sources to verify credibility']
                  },
                  capital: {
                    howToUse: 'Request ROI projections or business case frameworks with context about your AI initiative.',
                    capabilities: ['ROI calculation frameworks', 'Business case templates', 'SOX compliance checklists', 'Cost-benefit analysis'],
                    bestFor: ['Investment justification', 'Budget planning', 'Financial risk assessment', 'Stakeholder financial reporting'],
                    examplePrompts: [
                      'Build a business case for an AI-powered customer service chatbot',
                      'What ROI metrics should we track for our document automation project?',
                      'Help me calculate the 3-year TCO for implementing Claude Enterprise',
                      'What are the hidden costs of AI implementation I should budget for?'
                    ],
                    tips: ['Provide specific numbers (headcount, volume, costs) for more accurate projections']
                  },
                  guardian: {
                    howToUse: 'Consult on security, compliance, or vendor evaluations. Share technical details.',
                    capabilities: ['Security assessment frameworks', 'Compliance mapping', 'Shadow IT detection', 'Vendor security evaluation'],
                    bestFor: ['AI governance policies', 'Risk assessments', 'Technology audits', 'Regulatory compliance'],
                    examplePrompts: [
                      'Evaluate the security posture of this AI vendor for enterprise use',
                      'What governance policies should we have before deploying AI company-wide?',
                      'How do we detect and manage shadow AI usage?',
                      'Map our AI implementation to SOC 2 and GDPR requirements'
                    ],
                    tips: ['Share vendor security documentation for more specific assessments']
                  },
                  counselor: {
                    howToUse: 'Ask about contracts, compliance, or risk. Include stakeholder and jurisdiction context.',
                    capabilities: ['Contract review guidance', 'AI liability analysis', 'Privacy compliance', 'Regulatory navigation'],
                    bestFor: ['Vendor agreements', 'Data processing terms', 'IP considerations', 'Cross-border compliance'],
                    examplePrompts: [
                      'Review these AI vendor terms for red flags',
                      'Who owns the IP when we fine-tune a model on our data?',
                      'What are the GDPR implications of using AI for customer profiling?',
                      'How should we handle AI-generated content copyright issues?'
                    ],
                    tips: ['Specify jurisdictions when relevant', 'Note: Counselor provides guidance, not legal advice']
                  },
                  oracle: {
                    howToUse: 'Upload meeting transcripts to extract stakeholder positions and sentiment with quotes.',
                    capabilities: ['Transcript parsing', 'Sentiment extraction with quotes', 'Stakeholder position mapping', 'Power dynamics analysis'],
                    bestFor: ['Meeting debriefs', 'Stakeholder tracking', 'Decision archaeology', 'Communication patterns'],
                    examplePrompts: [
                      'Analyze this meeting transcript and identify key stakeholder positions',
                      'Who were the decision-makers and influencers in this meeting?',
                      'Extract action items and ownership from this transcript',
                      'What concerns did stakeholders raise about the AI initiative?'
                    ],
                    tips: ['Include speaker names in transcripts for better attribution', 'Provide context about the meeting purpose']
                  },
                  sage: {
                    howToUse: 'Discuss change strategies, adoption challenges, or incentive alignment. Sage designs people-first plans with human sovereignty in mind.',
                    capabilities: ['Change readiness assessment', 'Adoption strategy design', 'Incentive analysis (Buffett principle)', 'Human-centered AI framework', 'Resistance management', 'Champion program design'],
                    bestFor: ['Rollout planning', 'Adoption troubleshooting', 'Champion networks', 'Incentive realignment', 'Human sovereignty evaluation'],
                    examplePrompts: [
                      'Our AI adoption is stalling after initial excitement. What\'s going wrong?',
                      'Design a champion program that won\'t burn people out',
                      'How do we address employee fear about AI replacing jobs?',
                      'Evaluate whether this AI implementation preserves human sovereignty',
                      'Map the incentive conflicts in our AI rollout'
                    ],
                    tips: ['Share the actual incentive structures (how people are measured)', 'Be honest about organizational politics']
                  },
                  strategist: {
                    howToUse: 'Seek executive engagement or governance guidance. Share organizational context.',
                    capabilities: ['Stakeholder mapping', 'Political landscape analysis', 'Governance framework design', 'Executive communication'],
                    bestFor: ['Board presentations', 'Coalition building', 'Strategic alignment', 'Organizational change'],
                    examplePrompts: [
                      'How should we structure our AI steering committee?',
                      'Help me build executive sponsorship for our AI initiative',
                      'What governance framework should we adopt for AI?',
                      'Craft a board presentation on our AI strategy'
                    ],
                    tips: ['Share org chart context for better political navigation advice']
                  },
                  architect: {
                    howToUse: 'Discuss technical requirements or integration approaches with system details.',
                    capabilities: ['Architecture patterns', 'Integration design', 'Technology selection', 'Scalability planning'],
                    bestFor: ['System design', 'Build vs buy decisions', 'RAG implementation', 'API strategy'],
                    examplePrompts: [
                      'Should we build or buy our AI capabilities?',
                      'Design a RAG architecture for our document corpus',
                      'How should we integrate AI into our existing tech stack?',
                      'What infrastructure do we need for enterprise AI?'
                    ],
                    tips: ['Share your current tech stack for integration-aware recommendations']
                  },
                  operator: {
                    howToUse: 'Identify automation opportunities or metrics. Share workflow details.',
                    capabilities: ['Process mapping', 'Automation opportunity identification', 'KPI definition', 'Efficiency analysis'],
                    bestFor: ['Workflow optimization', 'Bottleneck identification', 'Metrics dashboards', 'SLA design'],
                    examplePrompts: [
                      'What processes in our workflow are good candidates for AI automation?',
                      'Help me define KPIs for our AI document processing system',
                      'How do we establish a baseline before AI implementation?',
                      'Map this workflow and identify efficiency opportunities'
                    ],
                    tips: ['Provide volume and frequency data for better prioritization']
                  },
                  pioneer: {
                    howToUse: 'Explore emerging tech or assess innovation maturity. Separates signal from noise.',
                    capabilities: ['Technology radar', 'Maturity assessment', 'Hype cycle positioning', 'Innovation portfolio'],
                    bestFor: ['Emerging tech evaluation', 'Proof of concept scoping', 'Future state planning', 'Competitive differentiation'],
                    examplePrompts: [
                      'Is this new AI technology ready for enterprise adoption?',
                      'What AI capabilities should we be watching for 2025?',
                      'Help me separate AI hype from practical capabilities',
                      'Scope a proof of concept for this emerging AI technology'
                    ],
                    tips: ['Specify your risk tolerance and innovation budget']
                  },
                  catalyst: {
                    howToUse: 'Draft communications or plan engagement. Share audience context.',
                    capabilities: ['Internal messaging', 'FAQ development', 'Anxiety addressing', 'Engagement campaigns'],
                    bestFor: ['Launch communications', 'Town hall prep', 'Newsletter content', 'Feedback collection'],
                    examplePrompts: [
                      'Draft an all-hands announcement for our AI rollout',
                      'Create an FAQ addressing common AI concerns',
                      'Design an engagement campaign for AI adoption',
                      'Help me prepare talking points for the AI town hall'
                    ],
                    tips: ['Share employee sentiment data if available']
                  },
                  scholar: {
                    howToUse: 'Design training or learning paths. Specify skill levels and objectives.',
                    capabilities: ['Curriculum design', 'Learning path creation', 'Skill gap analysis', 'Training effectiveness'],
                    bestFor: ['Onboarding programs', 'Upskilling initiatives', 'Certification paths', 'Knowledge transfer'],
                    examplePrompts: [
                      'Design an AI literacy curriculum for non-technical staff',
                      'Create a learning path for our AI champions',
                      'What skills should we prioritize in our AI training program?',
                      'How do we measure training effectiveness for AI skills?'
                    ],
                    tips: ['Specify current skill levels and available training time']
                  },
                  echo: {
                    howToUse: 'Analyze voice samples or review content for brand alignment. Provide examples.',
                    capabilities: ['Voice analysis', 'Style guide creation', 'Tone consistency', 'Brand alignment'],
                    bestFor: ['AI writing guidelines', 'Content review', 'Multi-channel consistency', 'Persona development'],
                    examplePrompts: [
                      'Analyze these writing samples and define our brand voice',
                      'Create AI writing guidelines that match our brand',
                      'Review this AI-generated content for brand alignment',
                      'How do we maintain authenticity with AI-assisted content?'
                    ],
                    tips: ['Provide multiple examples of content you consider on-brand']
                  },
                  nexus: {
                    howToUse: 'Map dependencies or explore feedback loops. Describe interconnected elements.',
                    capabilities: ['Dependency mapping', 'Feedback loop identification', 'Leverage point analysis', 'Consequence modeling'],
                    bestFor: ['Complex problem solving', 'Initiative interconnection', 'Risk cascades', 'System optimization'],
                    examplePrompts: [
                      'Map the dependencies between our AI initiatives',
                      'What unintended consequences might this AI deployment cause?',
                      'Identify the leverage points for maximum AI impact',
                      'How do these AI projects interact with each other?'
                    ],
                    tips: ['List all related initiatives and stakeholders for complete mapping']
                  },
                  coordinator: {
                    howToUse: 'Use Auto mode for routing or request multi-agent collaboration.',
                    capabilities: ['Query routing', 'Multi-agent synthesis', 'Context management', 'Response orchestration'],
                    bestFor: ['Complex queries', 'Cross-domain questions', 'Collaborative analysis', 'Holistic recommendations'],
                    examplePrompts: [
                      'I need help with an AI initiative - where should I start?',
                      'Get perspectives from multiple agents on this challenge',
                      'Route this question to the right specialist',
                      'Synthesize recommendations across domains'
                    ],
                    tips: ['Use Coordinator when unsure which specialist to engage']
                  },
                  facilitator: {
                    howToUse: 'Facilitator is automatically present in meeting rooms to orchestrate multi-agent discussions.',
                    capabilities: ['Meeting orchestration', 'Intent clarification', 'Agent routing', 'Balanced participation', 'Discussion synthesis'],
                    bestFor: ['Multi-agent meetings', 'Complex discussions', 'Cross-domain collaboration', 'Structured decision-making'],
                    examplePrompts: [
                      'Start a meeting to discuss our AI governance strategy',
                      'I need multiple perspectives on this adoption challenge',
                      'Help me think through this AI initiative from all angles',
                      'Facilitate a discussion between specialists'
                    ],
                    tips: ['Let Facilitator guide the flow - it will bring in specialists as needed']
                  },
                  reporter: {
                    howToUse: 'Reporter is automatically present in meetings. Ask for a summary, action items, or executive brief when you need unified documentation.',
                    capabilities: ['Meeting synthesis', 'Summary generation', 'Action item extraction', 'Executive briefs', 'Attribution tracking'],
                    bestFor: ['Meeting documentation', 'Stakeholder updates', 'Decision summaries', 'Action item tracking'],
                    examplePrompts: [
                      'Summarize what we discussed',
                      'What are our action items?',
                      'Give me an executive brief I can share with my VP',
                      'What were the key takeaways from this meeting?'
                    ],
                    tips: ['Ask for a brief when you need shareable output - Reporter will format it for stakeholders']
                  },
                  compass: {
                    howToUse: 'Tell Compass about your work conversationally. It extracts wins, asks clarifying questions, and updates your Performance Tracker. Use it before check-ins to prep talking points.',
                    capabilities: ['Win capture with impact metrics', 'Check-in preparation', 'Goal progress tracking', 'Strategic alignment validation', 'Reflection prompting', 'Performance Tracker updates'],
                    bestFor: ['Logging accomplishments', 'Manager 1:1 prep', 'Performance review prep', 'Goal tracking', 'Career reflection'],
                    examplePrompts: [
                      'I just shipped the invoice categorization pilot with Finance',
                      'Help me prep for my check-in with Chris tomorrow',
                      'Does this project align with our FY27 priorities?',
                      'What have I accomplished in the last two weeks?',
                      'I need to update my 30-60-90 day progress'
                    ],
                    tips: [
                      'Mention stakeholders by name - Compass tracks relationships',
                      'Include rough impact numbers (hours saved, etc.) for better documentation',
                      'Ask "how does this align?" before starting new initiatives'
                    ]
                  },
                  taskmaster: {
                    howToUse: 'Ask Taskmaster about your tasks from meetings, check your task status, or get focus guidance. Use the "Scan Recent Documents" button to discover tasks from your KB documents.',
                    capabilities: ['Task discovery from documents', 'Progress tracking by urgency', 'Focus guidance', 'Slippage detection', 'Task candidate review'],
                    bestFor: ['Finding tasks from meetings', 'Checking overdue items', 'Daily focus prioritization', 'Catching slipping commitments'],
                    examplePrompts: [
                      'What tasks did I pick up from last week\'s meetings?',
                      'What\'s my task status?',
                      'What should I focus on today?',
                      'Show me my overdue tasks',
                      'Review my pending task candidates'
                    ],
                    tips: [
                      'Scan documents regularly to catch commitments before they slip',
                      'Review task candidates to filter false positives',
                      'Ask for focus guidance when overwhelmed with tasks'
                    ]
                  }
                };
                const detail = usageDetails[agent.name.toLowerCase()];
                if (!detail) {
                  return <p className="text-secondary">Chat or include in meeting rooms for specialized insights.</p>;
                }

                return (
                  <div className="space-y-6">
                    <p className="text-secondary leading-relaxed">{detail.howToUse}</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-semibold text-primary mb-3">Capabilities</h4>
                        <ul className="space-y-1">
                          {detail.capabilities.map((cap, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                              <Circle className="w-1.5 h-1.5 text-primary mt-2 flex-shrink-0 fill-current" />
                              {cap}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold text-primary mb-3">Best For</h4>
                        <ul className="space-y-1">
                          {detail.bestFor.map((item, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                              <Circle className="w-1.5 h-1.5 text-primary mt-2 flex-shrink-0 fill-current" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-primary mb-3">Example Prompts</h4>
                      <div className="space-y-2">
                        {detail.examplePrompts.map((prompt, i) => (
                          <div key={i} className="bg-page border border-border rounded-lg px-4 py-2 text-sm text-secondary italic">
                            &ldquo;{prompt}&rdquo;
                          </div>
                        ))}
                      </div>
                    </div>

                    {detail.tips && (
                      <div className="pt-4 border-t border-border">
                        <h4 className="text-sm font-semibold text-primary mb-3">Pro Tips</h4>
                        <ul className="space-y-1">
                          {detail.tips.map((tip, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-secondary">
                              <ChevronRight className="w-3 h-3 text-primary mt-1 flex-shrink-0" />
                              {tip}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </details>
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
                      <div className="w-10 h-10 rounded-lg bg-card border border-border flex items-center justify-center">
                        <FileText className="w-5 h-5 text-secondary" />
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
                    <X className="w-5 h-5" />
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
                        <div className="w-10 h-10 rounded-lg bg-card border border-border flex items-center justify-center">
                          <FileText className="w-5 h-5 text-secondary" />
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

      {/* Career Status Report Modal (Compass only) */}
      {careerReport && (
        <CareerStatusReportModal
          report={careerReport}
          open={showCareerReportModal}
          onClose={() => setShowCareerReportModal(false)}
          onRegenerate={handleGenerateCareerReport}
          regenerating={careerReportLoading}
        />
      )}

      {/* Task Candidate Review Modal (Taskmaster only) */}
      {taskScanResult && taskScanResult.candidates.length > 0 && (
        <TaskCandidateReviewModal
          open={showCandidateReview}
          onClose={() => setShowCandidateReview(false)}
          onComplete={handleCandidateReviewComplete}
          candidates={taskScanResult.candidates}
        />
      )}
    </div>
  );
}
