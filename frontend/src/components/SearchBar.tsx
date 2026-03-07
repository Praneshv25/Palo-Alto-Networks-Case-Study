import { useState, useEffect } from 'react';

interface SearchBarProps {
  onFilterChange: (filters: {
    search: string;
    severity: string;
    status: string;
  }) => void;
}

export default function SearchBar({ onFilterChange }: SearchBarProps) {
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      onFilterChange({ search, severity, status });
    }, 300);
    return () => clearTimeout(timer);
  }, [search, severity, status, onFilterChange]);

  return (
    <div className="flex flex-wrap gap-3 mb-5">
      <div className="flex-1 min-w-[200px]">
        <input
          type="text"
          placeholder="Search reports (e.g. scam, fire, phishing)..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400 focus:border-transparent"
        />
      </div>
      <select
        value={severity}
        onChange={e => setSeverity(e.target.value)}
        className="px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
      >
        <option value="">All Severity</option>
        <option value="Low">Low</option>
        <option value="Medium">Medium</option>
        <option value="High">High</option>
      </select>
      <select
        value={status}
        onChange={e => setStatus(e.target.value)}
        className="px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
      >
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="resolved">Resolved</option>
      </select>
    </div>
  );
}
