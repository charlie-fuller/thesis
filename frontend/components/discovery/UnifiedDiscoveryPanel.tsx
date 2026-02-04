'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  ListChecks,
  Lightbulb,
  Users,
  Loader2,
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  FileText,
  Check
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
  const { user, session, loading: authLoading } = useAuth();

  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState<DiscoveryCounts>({ tasks: 0, projects: 0, stakeholders: 0, total: 0 });

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

  // Don't render while loading
  if (loading) return null;

  // Don't render if nothing to review (but show scanning status if active)
  if (counts.total === 0) {
    return (
      <div className="card p-6">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${scanning?.active ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-green-100 dark:bg-green-900/30'}`}>
            {scanning?.active ? (
              <Loader2 className="w-5 h-5 text-amber-600 dark:text-amber-400 animate-spin" />
            ) : (
              <Search className="w-5 h-5 text-green-600 dark:text-green-400" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-primary">Discovery Inbox</h3>
            {scanning?.active ? (
              <p className="text-sm text-secondary">
                {scanning.message || 'Analyzing documents for tasks, projects, stakeholders...'}
              </p>
            ) : (
              <p className="text-sm text-secondary">All caught up - no items to review</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Panel component for each category
  const renderPanel = (
    type: TabType,
    items: (TaskCandidate | ProjectCandidate | StakeholderCandidate)[],
    index: number,
    setIndex: (i: number) => void,
    icon: React.ElementType,
    label: string,
    colorClass: string,
    bgClass: string
  ) => {
    const item = items[index];
    if (!item) {
      return (
        <div className="flex-1 p-4 border border-default rounded-lg bg-page">
          <div className="flex items-center gap-2 mb-3">
            {React.createElement(icon, { className: `w-4 h-4 ${colorClass}` })}
            <span className="font-medium text-primary">{label}</span>
            <span className="ml-auto text-xs text-muted">0 items</span>
          </div>
          <p className="text-sm text-muted text-center py-4">No {label.toLowerCase()} to review</p>
        </div>
      );
    }

    const handlePanelAccept = async () => {
      setProcessing(true);
      try {
        let endpoint = '';
        let body: object = {};

        switch (type) {
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
        const singular = type === 'projects' ? 'Project' : type.slice(0, -1).charAt(0).toUpperCase() + type.slice(0, -1).slice(1);
        toast.success(`${singular} created`);

        // Remove from list and update counts
        const newList = items.filter((_, i) => i !== index);
        switch (type) {
          case 'tasks':
            setTasks(newList as TaskCandidate[]);
            setCounts(prev => ({ ...prev, tasks: prev.tasks - 1, total: prev.total - 1 }));
            if (index >= newList.length && index > 0) setTaskIndex(index - 1);
            break;
          case 'projects':
            setProjects(newList as ProjectCandidate[]);
            setCounts(prev => ({ ...prev, projects: prev.projects - 1, total: prev.total - 1 }));
            if (index >= newList.length && index > 0) setOppIndex(index - 1);
            break;
          case 'stakeholders':
            setStakeholders(newList as StakeholderCandidate[]);
            setCounts(prev => ({ ...prev, stakeholders: prev.stakeholders - 1, total: prev.total - 1 }));
            if (index >= newList.length && index > 0) setStakeholderIndex(index - 1);
            break;
        }
      } catch (err) {
        logger.error('Error accepting candidate:', err);
        toast.error('Failed to accept');
      } finally {
        setProcessing(false);
      }
    };

    const handlePanelReject = async () => {
      setProcessing(true);
      try {
        let endpoint = '';
        switch (type) {
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

        const newList = items.filter((_, i) => i !== index);
        switch (type) {
          case 'tasks':
            setTasks(newList as TaskCandidate[]);
            setCounts(prev => ({ ...prev, tasks: prev.tasks - 1, total: prev.total - 1 }));
            if (index >= newList.length && index > 0) setTaskIndex(index - 1);
            break;
          case 'projects':
            setProjects(newList as ProjectCandidate[]);
            setCounts(prev => ({ ...prev, projects: prev.projects - 1, total: prev.total - 1 }));
            if (index >= newList.length && index > 0) setOppIndex(index - 1);
            break;
          case 'stakeholders':
            setStakeholders(newList as StakeholderCandidate[]);
            setCounts(prev => ({ ...prev, stakeholders: prev.stakeholders - 1, total: prev.total - 1 }));
            if (index >= newList.length && index > 0) setStakeholderIndex(index - 1);
            break;
        }
      } catch (err) {
        logger.error('Error rejecting candidate:', err);
        toast.error('Failed to skip');
      } finally {
        setProcessing(false);
      }
    };

    return (
      <div className={`flex-1 border rounded-lg overflow-hidden ${bgClass}`}>
        {/* Panel Header */}
        <div className="flex items-center gap-2 p-3 border-b border-default bg-card">
          {React.createElement(icon, { className: `w-4 h-4 ${colorClass}` })}
          <span className="font-medium text-primary">{label}</span>
          <span className={`ml-auto px-1.5 py-0.5 text-xs rounded-full ${colorClass} bg-opacity-20`}>
            {items.length}
          </span>
        </div>

        {/* Panel Content */}
        <div className="p-3">
          {/* Source badge */}
          <div className="flex items-center gap-2 text-xs text-muted mb-2">
            <FileText className="w-3 h-3" />
            <span className="truncate">{item.source_document_name ?? 'Unknown source'}</span>
          </div>

          {/* Title */}
          <h4 className="font-semibold text-primary text-sm mb-1 line-clamp-1">
            {'title' in item ? item.title : (item as StakeholderCandidate).name}
          </h4>

          {/* Description preview */}
          {'description' in item && item.description && (
            <p className="text-xs text-secondary line-clamp-2 mb-2">
              {item.description}
            </p>
          )}

          {/* Type-specific metadata */}
          {type === 'tasks' && (
            <div className="flex gap-2 text-xs text-muted">
              {(item as TaskCandidate).team && <span>{(item as TaskCandidate).team}</span>}
            </div>
          )}
          {type === 'projects' && (
            <div className="flex gap-3 text-xs text-muted">
              <span>ROI: {(item as ProjectCandidate).suggested_roi_potential || 3}/5</span>
              <span>Effort: {(item as ProjectCandidate).suggested_effort || 3}/5</span>
            </div>
          )}
          {type === 'stakeholders' && (
            <div className="flex gap-2 flex-wrap">
              {(item as StakeholderCandidate).role && (
                <span className="text-xs bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">
                  {(item as StakeholderCandidate).role}
                </span>
              )}
              {(item as StakeholderCandidate).department && (
                <span className="text-xs bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded">
                  {(item as StakeholderCandidate).department}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Panel Actions */}
        <div className="flex items-center justify-between p-2 border-t border-default bg-page">
          <div className="flex items-center gap-1">
            <button
              onClick={() => index > 0 && setIndex(index - 1)}
              disabled={index === 0 || processing}
              className="p-1 text-muted hover:text-primary disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs text-secondary">{index + 1}/{items.length}</span>
            <button
              onClick={() => index < items.length - 1 && setIndex(index + 1)}
              disabled={index === items.length - 1 || processing}
              className="p-1 text-muted hover:text-primary disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handlePanelReject}
              disabled={processing}
              className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
              title="Skip"
            >
              <X className="w-4 h-4" />
            </button>
            <button
              onClick={handlePanelAccept}
              disabled={processing}
              className="p-1.5 text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition-colors disabled:opacity-50"
              title="Accept"
            >
              {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-default">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-amber-100 dark:bg-amber-900/30">
              <Search className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-primary">Discovery Inbox</h3>
              <p className="text-sm text-secondary">
                <span className="font-medium text-amber-600 dark:text-amber-400">{counts.total}</span> items to review
              </p>
            </div>
          </div>
          {scanning?.active && (
            <div className="flex items-center gap-2 text-xs text-amber-500">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>Analyzing {scanning.pending_documents} more...</span>
            </div>
          )}
        </div>
      </div>

      {/* Vertical Panel Layout */}
      <div className="p-4 space-y-4">
        {renderPanel(
          'tasks',
          tasks,
          taskIndex,
          setTaskIndex,
          ListChecks,
          'Tasks',
          'text-amber-500',
          'border-amber-500/30'
        )}
        {renderPanel(
          'projects',
          projects,
          oppIndex,
          setOppIndex,
          Lightbulb,
          'Projects',
          'text-emerald-500',
          'border-emerald-500/30'
        )}
        {renderPanel(
          'stakeholders',
          stakeholders,
          stakeholderIndex,
          setStakeholderIndex,
          Users,
          'Stakeholders',
          'text-purple-500',
          'border-purple-500/30'
        )}
      </div>
    </div>
  );
}
