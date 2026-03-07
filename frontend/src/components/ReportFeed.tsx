import { useState, useCallback } from 'react';
import { useReports } from '../hooks/useReports';
import ReportCard from './ReportCard';
import SearchBar from './SearchBar';

interface ReportFeedProps {
  userId: string;
}

export default function ReportFeed({ userId }: ReportFeedProps) {
  const [tab, setTab] = useState<'local' | 'digital'>('local');
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');

  const { reports, loading, error, updateLocalReport } = useReports({
    category: tab,
    search,
    severity,
    status,
  });

  const handleFilterChange = useCallback(
    (f: { search: string; severity: string; status: string }) => {
      setSearch(f.search);
      setSeverity(f.severity);
      setStatus(f.status);
    },
    []
  );

  return (
    <div>
      {/* Tab bar */}
      <div className="flex gap-1 mb-4">
        <button
          onClick={() => setTab('local')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            tab === 'local'
              ? 'bg-calm-600 text-white shadow-sm'
              : 'bg-white text-calm-600 border border-calm-200 hover:bg-calm-100'
          }`}
        >
          🏘️ Local Safety
        </button>
        <button
          onClick={() => setTab('digital')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            tab === 'digital'
              ? 'bg-calm-600 text-white shadow-sm'
              : 'bg-white text-calm-600 border border-calm-200 hover:bg-calm-100'
          }`}
        >
          🔒 Digital Defense
        </button>
      </div>

      <SearchBar onFilterChange={handleFilterChange} />

      {/* Report list */}
      {loading && (
        <div className="text-center py-12 text-calm-500 text-sm">Loading reports...</div>
      )}
      {error && (
        <div className="text-center py-12 text-danger text-sm">Error: {error}</div>
      )}
      {!loading && !error && reports.length === 0 && (
        <div className="text-center py-12 text-calm-500 text-sm">
          No reports found. The community is quiet — that's a good thing.
        </div>
      )}
      <div className="space-y-4">
        {reports.map(report => (
          <ReportCard
            key={report.id}
            report={report}
            userId={userId}
            onUpdate={updateLocalReport}
          />
        ))}
      </div>
    </div>
  );
}
