'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  ListChecks,
  Lightbulb,
  Users,
  ArrowRight,
  Loader2,
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  FileText,
  Link2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';
import { useAuth } from '@/contexts/AuthContext';

// Types
interface DiscoveryCounts {
  tasks: number;
  projects: number;
  stakeholders: number;
  total: number;
}

interface ScanningStatus {
  active: boolean;
  pending_documents: number;
  message?: string;
}

interface TaskCandidate {
  id: string;
  title: string;
  description?: string;
  assignee_name?: string;
  suggested_due_date?: string;
  team?: string;
  source_document_name?: string;
  confidence: string;
  created_at: string;
}

interface ProjectCandidate {
  id: string;
  title: string;
  description?: string;
  department?: string;
  source_document_name?: string;
  suggested_roi_potential?: number;
  suggested_effort?: number;
  suggested_alignment?: number;
  suggested_readiness?: number;
  confidence: string;
  matched_project_id?: string;
  match_reason?: string;
  created_at: string;
}

interface StakeholderCandidate {
  id: string;
  name: string;
  role?: string;
  department?: string;
  source_document_name?: string;
  initial_sentiment?: string;
  confidence: string;
  potential_match_stakeholder_id?: string;
  created_at: string;
}

interface DiscoveryAllResponse {
  tasks: TaskCandidate[];
  projects: ProjectCandidate[];
  stakeholders: StakeholderCandidate[];
  counts: DiscoveryCounts;
  scanning?: ScanningStatus;
}

type TabType = 'tasks' | 'projects' | 'stakeholders';

export default function UnifiedDiscoveryPanel() {
  const router = useRouter();
  const { user, session, loading: authLoading } = useAuth();

  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState<DiscoveryCounts>({ tasks: 0, projects: 0, stakeholders: 0, total: 0 });
  const [activeTab, setActiveTab] = useState<TabType>('tasks');
  const [expanded, setExpanded] = useState(false);

  // Candidate data
  const [tasks, setTasks] = useState<TaskCandidate[]>([]);
  const [projects, setProjects] = useState<ProjectCandidate[]>([]);
  const [stakeholders, setStakeholders] = useState<StakeholderCandidate[]>([]);

  // Current index for each tab
  const [taskIndex, setTaskIndex] = useState(0);
  const [oppIndex, setOppIndex] = useState(0);
  const [stakeholderIndex, setStakeholderIndex] = useState(0);

  const [processing, setProcessing] = useState(false);
  const [scanning, setScanning] = useState<ScanningStatus | null>(null);

  // Fetch counts and candidates
  const fetchData = useCallback(async () => {
    try {
      const data = await apiGet<DiscoveryAllResponse>('/api/discovery/all');
      setCounts(data.counts);
      setTasks(data.tasks);
      setProjects(data.projects);
      setStakeholders(data.stakeholders);
      setScanning(data.scanning || null);

      // Set active tab to first non-empty category
      if (data.tasks.length > 0) setActiveTab('tasks');
      else if (data.projects.length > 0) setActiveTab('projects');
      else if (data.stakeholders.length > 0) setActiveTab('stakeholders');
    } catch (err) {
      logger.error('Error fetching discovery data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading || !user || !session) return;
    fetchData();
    // Poll every 5 seconds to catch scanning status and new items quickly
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [authLoading, user, session, fetchData]);

  // Get current item based on active tab
  const getCurrentItem = () => {
    switch (activeTab) {
      case 'tasks':
        return tasks[taskIndex];
      case 'projects':
        return projects[oppIndex];
      case 'stakeholders':
        return stakeholders[stakeholderIndex];
      default:
        return null;
    }
  };

  const getCurrentList = () => {
    switch (activeTab) {
      case 'tasks':
        return tasks;
      case 'projects':
        return projects;
      case 'stakeholders':
        return stakeholders;
      default:
        return [];
    }
  };

  const getCurrentIndex = () => {
    switch (activeTab) {
      case 'tasks':
        return taskIndex;
      case 'projects':
        return oppIndex;
      case 'stakeholders':
        return stakeholderIndex;
      default:
        return 0;
    }
  };

  const setCurrentIndex = (index: number) => {
    switch (activeTab) {
      case 'tasks':
        setTaskIndex(index);
        break;
      case 'projects':
        setOppIndex(index);
        break;
      case 'stakeholders':
        setStakeholderIndex(index);
        break;
    }
  };

  // Navigation
  const goPrev = () => {
    const idx = getCurrentIndex();
    if (idx > 0) setCurrentIndex(idx - 1);
  };

  const goNext = () => {
    const idx = getCurrentIndex();
    const list = getCurrentList();
    if (idx < list.length - 1) setCurrentIndex(idx + 1);
  };

  // Accept/Reject handlers
  const handleAccept = async () => {
    const item = getCurrentItem();
    if (!item) return;

    setProcessing(true);
    try {
      let endpoint = '';
      let body: object = {};

      switch (activeTab) {
        case 'tasks':
          endpoint = `/api/tasks/candidates/${item.id}/accept`;
          body = { overrides: {} };
          break;
        case 'projects':
          endpoint = `/api/projects/candidates/${item.id}/accept`;
          body = { link_to_existing: false };
          break;
        case 'stakeholders':
          endpoint = `/api/stakeholders/candidates/${item.id}/accept`;
          body = {};
          break;
      }

      await apiPost(endpoint, body);
      const singular = activeTab === 'projects' ? 'Project' : activeTab.slice(0, -1).charAt(0).toUpperCase() + activeTab.slice(0, -1).slice(1);
      toast.success(`${singular} created`);

      // Remove from list and update counts
      const list = getCurrentList();
      const newList = list.filter((_, i) => i !== getCurrentIndex());

      switch (activeTab) {
        case 'tasks':
          setTasks(newList as TaskCandidate[]);
          setCounts(prev => ({ ...prev, tasks: prev.tasks - 1, total: prev.total - 1 }));
          if (taskIndex >= newList.length && taskIndex > 0) setTaskIndex(taskIndex - 1);
          break;
        case 'projects':
          setProjects(newList as ProjectCandidate[]);
          setCounts(prev => ({ ...prev, projects: prev.projects - 1, total: prev.total - 1 }));
          if (oppIndex >= newList.length && oppIndex > 0) setOppIndex(oppIndex - 1);
          break;
        case 'stakeholders':
          setStakeholders(newList as StakeholderCandidate[]);
          setCounts(prev => ({ ...prev, stakeholders: prev.stakeholders - 1, total: prev.total - 1 }));
          if (stakeholderIndex >= newList.length && stakeholderIndex > 0) setStakeholderIndex(stakeholderIndex - 1);
          break;
      }
    } catch (err) {
      logger.error('Error accepting candidate:', err);
      toast.error('Failed to accept');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    const item = getCurrentItem();
    if (!item) return;

    setProcessing(true);
    try {
      let endpoint = '';

      switch (activeTab) {
        case 'tasks':
          endpoint = `/api/tasks/candidates/${item.id}/reject`;
          break;
        case 'projects':
          endpoint = `/api/projects/candidates/${item.id}/reject`;
          break;
        case 'stakeholders':
          endpoint = `/api/stakeholders/candidates/${item.id}/reject`;
          break;
      }

      await apiPost(endpoint, { reason: 'Skipped from discovery panel' });
      toast.success('Skipped');

      // Remove from list and update counts
      const list = getCurrentList();
      const newList = list.filter((_, i) => i !== getCurrentIndex());

      switch (activeTab) {
        case 'tasks':
          setTasks(newList as TaskCandidate[]);
          setCounts(prev => ({ ...prev, tasks: prev.tasks - 1, total: prev.total - 1 }));
          if (taskIndex >= newList.length && taskIndex > 0) setTaskIndex(taskIndex - 1);
          break;
        case 'projects':
          setProjects(newList as ProjectCandidate[]);
          setCounts(prev => ({ ...prev, projects: prev.projects - 1, total: prev.total - 1 }));
          if (oppIndex >= newList.length && oppIndex > 0) setOppIndex(oppIndex - 1);
          break;
        case 'stakeholders':
          setStakeholders(newList as StakeholderCandidate[]);
          setCounts(prev => ({ ...prev, stakeholders: prev.stakeholders - 1, total: prev.total - 1 }));
          if (stakeholderIndex >= newList.length && stakeholderIndex > 0) setStakeholderIndex(stakeholderIndex - 1);
          break;
      }
    } catch (err) {
      logger.error('Error rejecting candidate:', err);
      toast.error('Failed to skip');
    } finally {
      setProcessing(false);
    }
  };

  // View full page for this category
  const handleViewAll = () => {
    switch (activeTab) {
      case 'tasks':
        router.push('/tasks');
        break;
      case 'projects':
        router.push('/projects');
        break;
      case 'stakeholders':
        router.push('/intelligence?tab=stakeholders');
        break;
    }
  };

  // Don't render while loading
  if (loading) return null;

  // Don't render if nothing to review (but show scanning status if active)
  if (counts.total === 0) {
    return (
      <div className="card p-6">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-lg ${scanning?.active ? 'bg-amber-500/10' : 'bg-green-500/10'}`}>
            {scanning?.active ? (
              <Loader2 className="w-6 h-6 text-amber-500 animate-spin" />
            ) : (
              <Search className="w-6 h-6 text-green-500" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-primary">Discovery Inbox</h3>
            {scanning?.active ? (
              <p className="text-sm text-amber-500">
                {scanning.message || 'Analyzing documents for tasks, projects, stakeholders...'}
              </p>
            ) : (
              <p className="text-sm text-green-500">All caught up - no items to review</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  const currentItem = getCurrentItem();
  const currentList = getCurrentList();
  const currentIndex = getCurrentIndex();

  const tabs = [
    { key: 'tasks' as TabType, label: 'Tasks', count: counts.tasks, icon: ListChecks, color: 'amber' },
    { key: 'projects' as TabType, label: 'Projects', count: counts.projects, icon: Lightbulb, color: 'emerald' },
    { key: 'stakeholders' as TabType, label: 'Stakeholders', count: counts.stakeholders, icon: Users, color: 'purple' },
  ];

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-default">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10">
              <Search className="w-5 h-5 text-amber-500" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-primary">Discovery Inbox</h3>
              <p className="text-sm text-secondary">
                <span className="font-medium text-amber-500">{counts.total}</span> items to review
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {scanning?.active && (
              <div className="flex items-center gap-2 text-xs text-amber-500">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Analyzing {scanning.pending_documents} more...</span>
              </div>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="px-3 py-1.5 text-sm font-medium text-secondary hover:text-primary transition-colors"
            >
              {expanded ? 'Collapse' : 'Expand'}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-default">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setActiveTab(tab.key);
              setCurrentIndex(0);
            }}
            disabled={tab.count === 0}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors relative ${
              activeTab === tab.key
                ? 'text-primary bg-card'
                : tab.count > 0
                ? 'text-secondary hover:text-primary bg-page'
                : 'text-muted bg-page cursor-not-allowed'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span className={`px-1.5 py-0.5 text-xs rounded-full ${
                  activeTab === tab.key
                    ? `bg-${tab.color}-500/20 text-${tab.color}-500`
                    : 'bg-gray-200 dark:bg-gray-700 text-secondary'
                }`}>
                  {tab.count}
                </span>
              )}
            </div>
            {activeTab === tab.key && (
              <div className={`absolute bottom-0 left-0 right-0 h-0.5 bg-${tab.color}-500`} />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {currentList.length > 0 && currentItem && (
        <div className={`transition-all duration-300 ${expanded ? 'max-h-[600px]' : 'max-h-[200px]'}`}>
          {/* Quick preview */}
          <div className="p-4">
            {/* Source badge */}
            <div className="flex items-center gap-2 text-xs text-muted mb-2">
              <FileText className="w-3 h-3" />
              <span>{'source_document_name' in currentItem ? (currentItem as any).source_document_name : 'Unknown source'}</span>
              <span className={`ml-auto px-2 py-0.5 rounded font-medium ${
                currentItem.confidence === 'high'
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-yellow-500/20 text-yellow-400'
              }`}>
                {currentItem.confidence}
              </span>
            </div>

            {/* Title */}
            <h4 className="font-semibold text-primary mb-1">
              {'title' in currentItem ? currentItem.title : (currentItem as StakeholderCandidate).name}
            </h4>

            {/* Description preview */}
            {'description' in currentItem && currentItem.description && (
              <p className="text-sm text-secondary line-clamp-2">
                {currentItem.description}
              </p>
            )}

            {/* Stakeholder role/dept */}
            {activeTab === 'stakeholders' && (
              <div className="flex gap-2 mt-2">
                {(currentItem as StakeholderCandidate).role && (
                  <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                    {(currentItem as StakeholderCandidate).role}
                  </span>
                )}
                {(currentItem as StakeholderCandidate).department && (
                  <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded">
                    {(currentItem as StakeholderCandidate).department}
                  </span>
                )}
              </div>
            )}

            {/* Opportunity scores preview */}
            {activeTab === 'projects' && (
              <div className="flex gap-4 mt-2 text-xs text-muted">
                <span>ROI: {(currentItem as ProjectCandidate).suggested_roi_potential || 3}/5</span>
                <span>Effort: {(currentItem as ProjectCandidate).suggested_effort || 3}/5</span>
              </div>
            )}

            {/* Task team/due date */}
            {activeTab === 'tasks' && (
              <div className="flex gap-3 mt-2 text-xs text-muted">
                {(currentItem as TaskCandidate).team && (
                  <span>Team: {(currentItem as TaskCandidate).team}</span>
                )}
                {(currentItem as TaskCandidate).suggested_due_date && (
                  <span>Due: {(currentItem as TaskCandidate).suggested_due_date}</span>
                )}
              </div>
            )}

            {/* Match warning for projects */}
            {activeTab === 'projects' && (currentItem as ProjectCandidate).matched_project_id && (
              <div className="mt-2 flex items-center gap-1 text-xs text-amber-500">
                <Link2 className="w-3 h-3" />
                <span>Potential duplicate detected</span>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between p-4 border-t border-default bg-page">
            <div className="flex items-center gap-2">
              <button
                onClick={goPrev}
                disabled={currentIndex === 0 || processing}
                className="p-1.5 text-muted hover:text-primary disabled:opacity-30 transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-sm text-secondary">
                {currentIndex + 1} of {currentList.length}
              </span>
              <button
                onClick={goNext}
                disabled={currentIndex === currentList.length - 1 || processing}
                className="p-1.5 text-muted hover:text-primary disabled:opacity-30 transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleReject}
                disabled={processing}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
              >
                <X className="w-4 h-4" />
                Skip
              </button>
              <button
                onClick={handleAccept}
                disabled={processing}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Accept
              </button>
              <button
                onClick={handleViewAll}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-secondary hover:text-primary transition-colors"
              >
                View All
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
