'use client';

import { useState } from 'react';
import {
  User,
  Building,
  Briefcase,
  AlertCircle,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Check,
  X,
  GitMerge,
  FileText,
  Loader2
} from 'lucide-react';

export interface StakeholderCandidate {
  id: string;
  name: string;
  role: string | null;
  department: string | null;
  organization: string | null;
  email: string | null;
  key_concerns: string[];
  interests: string[];
  initial_sentiment: string | null;
  influence_level: string | null;
  source_document_id: string | null;
  source_document_name: string | null;
  source_text: string | null;
  extraction_context: string | null;
  related_opportunity_ids: string[];
  related_task_ids: string[];
  status: string;
  confidence: string;
  potential_match_stakeholder_id: string | null;
  potential_match_name: string | null;
  matched_candidate_id: string | null;
  match_confidence: number | null;
  match_reason: string | null;
  created_at: string;
}

interface StakeholderCandidateCardProps {
  candidate: StakeholderCandidate;
  onAccept: (id: string, overrides?: { name?: string; role?: string; department?: string }) => Promise<void>;
  onReject: (id: string, reason?: string) => Promise<void>;
  onMerge: (id: string, targetStakeholderId: string) => Promise<void>;
  stakeholders?: Array<{ id: string; name: string }>;
}

export default function StakeholderCandidateCard({
  candidate,
  onAccept,
  onReject,
  onMerge,
  stakeholders = []
}: StakeholderCandidateCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showMergeSelect, setShowMergeSelect] = useState(false);
  const [selectedMergeTarget, setSelectedMergeTarget] = useState<string>('');

  const getSentimentIcon = (sentiment: string | null) => {
    switch (sentiment) {
      case 'positive':
        return <ArrowUpRight className="w-4 h-4 text-green-500" />;
      case 'negative':
        return <ArrowDownRight className="w-4 h-4 text-red-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSentimentBadge = (sentiment: string | null) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
      case 'negative':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
    }
  };

  const getInfluenceBadge = (influence: string | null) => {
    switch (influence) {
      case 'high':
        return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300';
      case 'low':
        return 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300';
      default:
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300';
    }
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300';
      case 'low':
        return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300';
      default:
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300';
    }
  };

  const handleAccept = async () => {
    setIsProcessing(true);
    try {
      await onAccept(candidate.id);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    setIsProcessing(true);
    try {
      await onReject(candidate.id);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleMerge = async () => {
    if (!selectedMergeTarget) return;
    setIsProcessing(true);
    try {
      await onMerge(candidate.id, selectedMergeTarget);
    } finally {
      setIsProcessing(false);
      setShowMergeSelect(false);
    }
  };

  return (
    <div className="card p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <User className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-primary">{candidate.name}</h3>
            {candidate.role && (
              <p className="text-sm text-secondary">{candidate.role}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded-full ${getConfidenceBadge(candidate.confidence)}`}>
            {candidate.confidence} confidence
          </span>
        </div>
      </div>

      {/* Basic Info */}
      <div className="space-y-2 text-sm mb-4">
        {candidate.department && (
          <div className="flex items-center gap-2 text-secondary">
            <Building className="w-4 h-4" />
            <span className="capitalize">{candidate.department}</span>
          </div>
        )}
        {candidate.organization && (
          <div className="flex items-center gap-2 text-secondary">
            <Briefcase className="w-4 h-4" />
            <span>{candidate.organization}</span>
          </div>
        )}
        {candidate.source_document_name && (
          <div className="flex items-center gap-2 text-secondary">
            <FileText className="w-4 h-4" />
            <span className="truncate" title={candidate.source_document_name}>
              {candidate.source_document_name}
            </span>
          </div>
        )}
      </div>

      {/* Sentiment & Influence */}
      <div className="flex flex-wrap gap-2 mb-4">
        {candidate.initial_sentiment && (
          <span className={`px-2 py-1 text-xs rounded-full flex items-center gap-1 ${getSentimentBadge(candidate.initial_sentiment)}`}>
            {getSentimentIcon(candidate.initial_sentiment)}
            {candidate.initial_sentiment}
          </span>
        )}
        {candidate.influence_level && (
          <span className={`px-2 py-1 text-xs rounded-full ${getInfluenceBadge(candidate.influence_level)}`}>
            {candidate.influence_level} influence
          </span>
        )}
      </div>

      {/* Potential Match Warning */}
      {(candidate.potential_match_stakeholder_id || candidate.matched_candidate_id) && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 mb-4">
          <div className="flex items-center gap-2 text-amber-700 dark:text-amber-300 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>
              {candidate.potential_match_stakeholder_id ? (
                <>Potential match: <strong>{candidate.potential_match_name}</strong></>
              ) : (
                <>Similar to pending candidate</>
              )}
              {candidate.match_confidence && (
                <span className="text-amber-600 dark:text-amber-400 ml-1">
                  ({Math.round(candidate.match_confidence * 100)}% match)
                </span>
              )}
            </span>
          </div>
          {candidate.match_reason && (
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
              {candidate.match_reason}
            </p>
          )}
        </div>
      )}

      {/* Expandable Details */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-sm text-brand hover:underline mb-3"
      >
        {isExpanded ? 'Show less' : 'Show details'}
      </button>

      {isExpanded && (
        <div className="space-y-3 pt-3 border-t border-default">
          {/* Concerns */}
          {candidate.key_concerns.length > 0 && (
            <div>
              <div className="text-xs text-orange-600 dark:text-orange-400 font-medium mb-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Key Concerns
              </div>
              <div className="flex flex-wrap gap-1">
                {candidate.key_concerns.map((concern, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 rounded">
                    {concern}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Interests */}
          {candidate.interests.length > 0 && (
            <div>
              <div className="text-xs text-green-600 dark:text-green-400 font-medium mb-1 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                Interests
              </div>
              <div className="flex flex-wrap gap-1">
                {candidate.interests.map((interest, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded">
                    {interest}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source Text */}
          {candidate.source_text && (
            <div>
              <div className="text-xs text-secondary font-medium mb-1">Evidence</div>
              <p className="text-sm text-secondary italic bg-secondary/5 p-2 rounded">
                &ldquo;{candidate.source_text}&rdquo;
              </p>
            </div>
          )}

          {/* Extraction Context */}
          {candidate.extraction_context && (
            <div>
              <div className="text-xs text-secondary font-medium mb-1">Meeting Context</div>
              <p className="text-sm text-secondary">
                {candidate.extraction_context}
              </p>
            </div>
          )}

          {/* Related Entities */}
          {(candidate.related_opportunity_ids.length > 0 || candidate.related_task_ids.length > 0) && (
            <div>
              <div className="text-xs text-secondary font-medium mb-1">Will Link To</div>
              <div className="flex gap-2 text-xs text-secondary">
                {candidate.related_opportunity_ids.length > 0 && (
                  <span>{candidate.related_opportunity_ids.length} opportunities</span>
                )}
                {candidate.related_task_ids.length > 0 && (
                  <span>{candidate.related_task_ids.length} tasks</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-2 mt-4 pt-4 border-t border-default">
        {showMergeSelect ? (
          <div className="flex items-center gap-2 w-full">
            <select
              value={selectedMergeTarget}
              onChange={(e) => setSelectedMergeTarget(e.target.value)}
              className="flex-1 px-2 py-1 text-sm border border-default rounded bg-card text-primary"
            >
              <option value="">Select stakeholder...</option>
              {stakeholders.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            <button
              onClick={handleMerge}
              disabled={!selectedMergeTarget || isProcessing}
              className="p-1.5 rounded bg-purple-500 text-white disabled:opacity-50"
            >
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setShowMergeSelect(false)}
              className="p-1.5 rounded bg-secondary text-secondary"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
            >
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
              Reject
            </button>
            {(candidate.potential_match_stakeholder_id || stakeholders.length > 0) && (
              <button
                onClick={() => {
                  if (candidate.potential_match_stakeholder_id) {
                    setSelectedMergeTarget(candidate.potential_match_stakeholder_id);
                  }
                  setShowMergeSelect(true);
                }}
                disabled={isProcessing}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded transition-colors disabled:opacity-50"
              >
                <GitMerge className="w-4 h-4" />
                Merge
              </button>
            )}
            <button
              onClick={handleAccept}
              disabled={isProcessing}
              className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-500 hover:bg-green-600 text-white rounded transition-colors disabled:opacity-50"
            >
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              Accept
            </button>
          </>
        )}
      </div>
    </div>
  );
}
