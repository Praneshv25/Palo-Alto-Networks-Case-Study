import { useState } from 'react';
import type { SafetyReport, TrustLabel } from '../types/report';
import TrustBadge from './TrustBadge';
import VoteControls from './VoteControls';
import { updateReport } from '../lib/api';

const SEVERITY_STYLES = {
  Low: 'bg-green-100 text-green-800 border-green-300',
  Medium: 'bg-amber-100 text-amber-800 border-amber-300',
  High: 'bg-red-100 text-red-800 border-red-300',
};

interface ReportCardProps {
  report: SafetyReport;
  userId: string;
  onUpdate: (id: string, updates: Partial<SafetyReport>) => void;
}

export default function ReportCard({ report, userId, onUpdate }: ReportCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [resolving, setResolving] = useState(false);
  const isFlagged = report.trustLabel === 'flagged';
  const isResolved = report.status === 'Resolved';

  const handleResolve = async () => {
    setResolving(true);
    try {
      const updated = await updateReport(report.id, {
        status: 'Resolved',
        resolution_note: 'Resolved by community member.',
      });
      onUpdate(report.id, { status: updated.status });
    } catch {
      // silently fail
    } finally {
      setResolving(false);
    }
  };

  const handleVoteUpdate = (upvotes: number, downvotes: number, trustLabel: TrustLabel) => {
    onUpdate(report.id, { upvotes, downvotes, trustLabel });
  };

  const timeAgo = (() => {
    if (!report.timestamp) return '';
    const diff = Date.now() - new Date(report.timestamp).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return new Date(report.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  })();

  return (
    <article
      data-testid="report-card"
      className={`bg-white rounded-xl border border-calm-200 shadow-sm transition-opacity ${
        isFlagged ? 'opacity-50' : ''
      } ${isResolved ? 'opacity-70' : ''}`}
    >
      <div className="p-4">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              data-testid="severity-badge"
              className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${SEVERITY_STYLES[report.severity]}`}
            >
              {report.severity}
            </span>
            <TrustBadge trustLabel={report.trustLabel} />
            {isResolved && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-calm-100 text-calm-700 border border-calm-300">
                Resolved
              </span>
            )}
          </div>
          <span className="text-xs text-calm-500 whitespace-nowrap">{timeAgo}</span>
        </div>

        {/* Title & summary */}
        <h3 className="text-base font-semibold text-calm-900 mb-1">{report.title}</h3>
        <p className="text-sm text-calm-700 leading-relaxed mb-3">{report.summary}</p>

        {/* Checklist */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs font-medium text-calm-600 hover:text-calm-800 mb-2 flex items-center gap-1"
        >
          <span className={`transition-transform ${expanded ? 'rotate-90' : ''}`}>▸</span>
          Action Checklist ({report.checklist.length})
        </button>
        {expanded && (
          <ol className="list-decimal list-inside text-sm text-calm-700 space-y-1 mb-3 pl-1">
            {report.checklist.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ol>
        )}

        {/* Footer: votes + resolve */}
        <div className="flex items-center justify-between pt-2 border-t border-calm-100">
          <VoteControls
            reportId={report.id}
            userId={userId}
            upvotes={report.upvotes}
            downvotes={report.downvotes}
            onVoteUpdate={handleVoteUpdate}
          />
          {!isResolved && (
            <button
              onClick={handleResolve}
              disabled={resolving}
              className="text-xs font-medium text-calm-600 hover:text-calm-800 px-3 py-1 rounded hover:bg-calm-100 transition-colors"
            >
              {resolving ? 'Resolving...' : 'Mark Resolved'}
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
