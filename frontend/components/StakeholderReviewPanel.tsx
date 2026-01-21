'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Users, ArrowRight } from 'lucide-react';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';
import { useAuth } from '@/contexts/AuthContext';

interface CandidateCountResponse {
  count: number;
}

export default function StakeholderReviewPanel() {
  const router = useRouter();
  const { user, session, loading: authLoading } = useAuth();
  const [pendingCount, setPendingCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading || !user || !session) {
      return;
    }

    fetchData();
    // Refresh every 2 minutes
    const interval = setInterval(fetchData, 120000);
    return () => clearInterval(interval);
  }, [authLoading, user, session]);

  const fetchData = async () => {
    try {
      const countData = await apiGet<CandidateCountResponse>('/api/stakeholders/candidates/count');
      setPendingCount(countData.count ?? 0);
    } catch (err) {
      logger.error('Error fetching stakeholder review data:', err);
      setPendingCount(0);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewStakeholders = () => {
    router.push('/intelligence');
  };

  // Don't render anything while loading to prevent flash
  if (loading) {
    return null;
  }

  const hasStakeholdersToReview = pendingCount !== null && pendingCount > 0;

  // Only show panel if there are stakeholders to review
  if (!hasStakeholdersToReview) {
    return null;
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-blue-500/10">
            <Users className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-primary">Stakeholders to Review</h3>
            <p className="text-sm text-secondary">
              <span className="font-medium text-blue-500">{pendingCount}</span>
              {' '}stakeholder candidate{pendingCount !== 1 ? 's' : ''} discovered from meetings
            </p>
          </div>
        </div>

        <button
          onClick={handleReviewStakeholders}
          className="flex items-center gap-2 px-4 py-2 font-medium rounded-lg transition-colors bg-blue-500 hover:bg-blue-600 text-white"
        >
          Review Stakeholders
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
