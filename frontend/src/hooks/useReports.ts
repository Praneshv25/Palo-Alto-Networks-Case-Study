import { useState, useEffect, useCallback } from 'react';
import type { SafetyReport } from '../types/report';
import { getReports } from '../lib/api';

interface Filters {
  category?: string;
  search?: string;
  status?: string;
  severity?: string;
  lat?: number | null;
  lng?: number | null;
  radius_km?: number;
}

export function useReports(filters: Filters = {}) {
  const [reports, setReports] = useState<SafetyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {};
      if (filters.category) params.category = filters.category;
      if (filters.search) params.search = filters.search;
      if (filters.status) params.status = filters.status;
      if (filters.severity) params.severity = filters.severity;
      if (filters.lat != null && filters.lng != null) {
        params.lat = filters.lat;
        params.lng = filters.lng;
        params.radius_km = filters.radius_km ?? 10;
      }
      const data = await getReports(params as Parameters<typeof getReports>[0]);
      setReports(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  }, [filters.category, filters.search, filters.status, filters.severity, filters.lat, filters.lng, filters.radius_km]);

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
