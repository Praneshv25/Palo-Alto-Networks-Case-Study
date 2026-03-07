import { useState } from 'react';
import { voteOnReport } from '../lib/api';
import type { TrustLabel } from '../types/report';

interface VoteControlsProps {
  reportId: string;
  userId: string;
  upvotes: number;
  downvotes: number;
  onVoteUpdate: (upvotes: number, downvotes: number, trustLabel: TrustLabel) => void;
}

export default function VoteControls({
  reportId,
  userId,
  upvotes,
  downvotes,
  onVoteUpdate,
}: VoteControlsProps) {
  const [userVote, setUserVote] = useState<'up' | 'down' | null>(null);
  const [localUp, setLocalUp] = useState(upvotes);
  const [localDown, setLocalDown] = useState(downvotes);
  const [submitting, setSubmitting] = useState(false);

  const handleVote = async (type: 'up' | 'down') => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const res = await voteOnReport(reportId, { user_id: userId, vote_type: type });
      setLocalUp(res.upvotes);
      setLocalDown(res.downvotes);
      setUserVote(res.userVote);
      onVoteUpdate(res.upvotes, res.downvotes, res.trustLabel);
    } catch {
      // silently fail
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex items-center gap-3 text-sm">
      <button
        onClick={() => handleVote('up')}
        disabled={submitting}
        className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
          userVote === 'up'
            ? 'bg-green-100 text-green-700 font-semibold'
            : 'text-calm-600 hover:bg-calm-100'
        }`}
        title="I can confirm this"
      >
        <span className="text-base">▲</span>
        <span>{localUp}</span>
      </button>
      <button
        onClick={() => handleVote('down')}
        disabled={submitting}
        className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
          userVote === 'down'
            ? 'bg-red-100 text-red-700 font-semibold'
            : 'text-calm-600 hover:bg-calm-100'
        }`}
        title="This seems inaccurate"
      >
        <span className="text-base">▼</span>
        <span>{localDown}</span>
      </button>
    </div>
  );
}
