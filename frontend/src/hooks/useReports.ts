import { useState, useEffect, useCallback } from 'react';
import type { SafetyReport } from '../types/report';
import { getReports } from '../lib/api';

interface Filters {
  category?: string;
  search?: string;
  status?: string;
  severity?: string;
}

export function useReports(filters: Filters = {}) {
  const [reports, setReports] = useState<SafetyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const clean: Record<string, string> = {};
      if (filters.category) clean.category = filters.category;
      if (filters.search) clean.search = filters.search;
      if (filters.status) clean.status = filters.status;
      if (filters.severity) clean.severity = filters.severity;
      const data = await getReports(clean);
      setReports(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  }, [filters.category, filters.search, filters.status, filters.severity]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const updateLocalReport = useCallback((id: string, updates: Partial<SafetyReport>) => {
    setReports(prev =>
      prev.map(r => (r.id === id ? { ...r, ...updates } : r))
    );
  }, []);

  return { reports, loading, error, refetch: fetchReports, updateLocalReport };
}
