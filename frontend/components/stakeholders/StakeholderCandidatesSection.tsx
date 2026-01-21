'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, RefreshCw, Users, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { apiGet, apiPost } from '@/lib/api';
import { logger } from '@/lib/logger';
import StakeholderCandidateCard, { StakeholderCandidate } from './StakeholderCandidateCard';

interface ScanResult {
  message: string;
  documents_scanned: number;
  stakeholders_found: number;
  candidates_created: number;
  duplicates_found: number;
  errors: string[];
}

interface StakeholderCandidatesSectionProps {
  onStakeholderCreated?: () => void;
  stakeholders?: Array<{ id: string; name: string }>;
}

export default function StakeholderCandidatesSection({
  onStakeholderCreated,
  stakeholders = []
}: StakeholderCandidatesSectionProps) {
  const [candidates, setCandidates] = useState<StakeholderCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forceRescan, setForceRescan] = useState(false);

  const fetchCandidates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiGet<StakeholderCandidate[]>('/api/stakeholders/candidates?status=pending');
      setCandidates(data || []);
    } catch (err) {
      logger.error('Error fetching stakeholder candidates:', err);
      setError(err instanceof Error ? err.message : 'Failed to load candidates');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  const handleScan = async () => {
    try {
      setScanning(true);
      setScanResult(null);
      setError(null);

      const result = await apiPost<ScanResult>('/api/stakeholders/scan-documents', {
        force_rescan: forceRescan,
        since_days: 90,
        limit: 20
      });

      setScanResult(result);
      await fetchCandidates();
    } catch (err) {
      logger.error('Error scanning documents:', err);
      setError(err instanceof Error ? err.message : 'Failed to scan documents');
    } finally {
      setScanning(false);
    }
  };

  const handleAccept = async (id: string, overrides?: { name?: string; role?: string; department?: string }) => {
    try {
      await apiPost(`/api/stakeholders/candidates/${id}/accept`, overrides || {});
      setCandidates(prev => prev.filter(c => c.id !== id));
      onStakeholderCreated?.();
    } catch (err) {
      logger.error('Error accepting candidate:', err);
      throw err;
    }
  };

  const handleReject = async (id: string, reason?: string) => {
    try {
      await apiPost(`/api/stakeholders/candidates/${id}/reject`, { reason });
      setCandidates(prev => prev.filter(c => c.id !== id));
    } catch (err) {
      logger.error('Error rejecting candidate:', err);
      throw err;
    }
  };

  const handleMerge = async (id: string, targetStakeholderId: string) => {
    try {
      await apiPost(`/api/stakeholders/candidates/${id}/merge`, {
        target_stakeholder_id: targetStakeholderId,
        update_concerns: true,
        update_interests: true
      });
      setCandidates(prev => prev.filter(c => c.id !== id));
      onStakeholderCreated?.();
    } catch (err) {
      logger.error('Error merging candidate:', err);
      throw err;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Scan Controls */}
      <div className="card p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <Search className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-primary">Stakeholder Discovery</h3>
              <p className="text-sm text-secondary">
                Scan meeting documents to discover new stakeholders
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={forceRescan}
                onChange={(e) => setForceRescan(e.target.checked)}
                className="rounded border-gray-300"
              />
              Rescan all docs
            </label>
            <button
              onClick={handleScan}
              disabled={scanning}
              className="flex items-center gap-2 px-4 py-2 bg-brand hover:bg-brand/90 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {scanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Scan for Stakeholders
                </>
              )}
            </button>
          </div>
        </div>

        {/* Scan Result */}
        {scanResult && (
          <div className={`mt-4 p-3 rounded-lg flex items-start gap-2 ${
            scanResult.candidates_created > 0
              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
              : 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
          }`}>
            {scanResult.candidates_created > 0 ? (
              <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-medium">
                Scanned {scanResult.documents_scanned} document{scanResult.documents_scanned !== 1 ? 's' : ''}
              </p>
              <p className="text-sm">
                Found {scanResult.stakeholders_found} stakeholder{scanResult.stakeholders_found !== 1 ? 's' : ''},
                created {scanResult.candidates_created} new candidate{scanResult.candidates_created !== 1 ? 's' : ''}
                {scanResult.duplicates_found > 0 && ` (${scanResult.duplicates_found} already tracked)`}
              </p>
              {scanResult.errors.length > 0 && (
                <p className="text-sm text-amber-600 dark:text-amber-400 mt-1">
                  {scanResult.errors.length} error{scanResult.errors.length !== 1 ? 's' : ''} occurred
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">{error}</p>
          <button onClick={fetchCandidates} className="mt-2 text-sm text-red-600 dark:text-red-400 hover:underline">
            Try again
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-brand" />
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && candidates.length === 0 && (
        <div className="card p-12 text-center">
          <div className="flex justify-center mb-4">
            <Users className="w-12 h-12 text-muted" />
          </div>
          <h3 className="text-lg font-semibold text-primary mb-2">
            No pending candidates
          </h3>
          <p className="text-secondary mb-4">
            Scan your meeting documents to discover stakeholders automatically.
          </p>
        </div>
      )}

      {/* Candidates Grid */}
      {!loading && candidates.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-primary">
              Pending Candidates ({candidates.length})
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {candidates.map(candidate => (
              <StakeholderCandidateCard
                key={candidate.id}
                candidate={candidate}
                onAccept={handleAccept}
                onReject={handleReject}
                onMerge={handleMerge}
                stakeholders={stakeholders}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
