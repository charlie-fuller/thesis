'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ListChecks, ArrowRight, Loader2 } from 'lucide-react';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';
import { useAuth } from '@/contexts/AuthContext';

interface CandidateCountResponse {
  success: boolean;
  pending_count: number;
}

export default function TaskReviewPanel() {
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
      const countData = await apiGet<CandidateCountResponse>('/api/tasks/candidates/count');

      if (countData.success) {
        setPendingCount(countData.pending_count);
      }
    } catch (err) {
      logger.error('Error fetching task review data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessTasks = () => {
    router.push('/tasks');
  };

  // Don't show panel if no pending tasks
  if (!loading && pendingCount === 0) {
    return null;
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-amber-500/10">
            <ListChecks className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-primary">Tasks to Review</h3>
            <p className="text-sm text-secondary">
              {loading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Loading...
                </span>
              ) : (
                <>
                  <span className="font-medium text-amber-500">{pendingCount}</span>
                  {' '}task candidate{pendingCount !== 1 ? 's' : ''} discovered from your documents
                </>
              )}
            </p>
          </div>
        </div>

        <button
          onClick={handleProcessTasks}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 text-white font-medium rounded-lg transition-colors"
        >
          Process Tasks
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
