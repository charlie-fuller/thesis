'use client';

import { useState, useEffect, useCallback, useRef, DependencyList } from 'react';
import { apiGet, APIError } from '@/lib/api';
import { logger } from '@/lib/logger';

interface UseFetchDataOptions {
  /** Whether to fetch immediately on mount (default: true) */
  immediate?: boolean;
  /** Log prefix for debugging */
  logPrefix?: string;
}

interface UseFetchDataResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Custom hook for data fetching with loading/error states.
 * Eliminates boilerplate across dashboard card components.
 *
 * @param endpoint - API endpoint to fetch from
 * @param deps - Dependencies that trigger a refetch when changed
 * @param options - Additional options
 *
 * @example
 * const { data, loading, error, refetch } = useFetchData<UserData>(
 *   `/api/users/${userId}`,
 *   [userId]
 * );
 */
export function useFetchData<T>(
  endpoint: string,
  deps: DependencyList = [],
  options: UseFetchDataOptions = {}
): UseFetchDataResult<T> {
  const { immediate = true, logPrefix } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const result = await apiGet<T>(endpoint);

      if (mountedRef.current) {
        if (logPrefix) {
          logger.debug(`${logPrefix} Response:`, result);
        }
        setData(result);
      }
    } catch (err) {
      if (mountedRef.current) {
        if (logPrefix) {
          logger.error(`${logPrefix} Error:`, err);
        }
        if (err instanceof APIError) {
          setError(err.message);
        } else {
          setError(err instanceof Error ? err.message : 'An error occurred');
        }
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, logPrefix, ...deps]);

  useEffect(() => {
    mountedRef.current = true;

    if (immediate) {
      fetchData();
    }

    return () => {
      mountedRef.current = false;
    };
  }, [fetchData, immediate]);

  return { data, loading, error, refetch: fetchData };
}

export default useFetchData;
