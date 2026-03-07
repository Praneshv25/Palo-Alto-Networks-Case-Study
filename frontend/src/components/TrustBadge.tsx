import type { TrustLabel } from '../types/report';

const CONFIG: Record<TrustLabel, { label: string; icon: string; classes: string }> = {
  ai_generated: {
    label: 'AI Generated',
    icon: '✦',
    classes: 'bg-blue-50 text-blue-700 border-blue-200',
  },
  pending_verification: {
    label: 'Pending Verification',
    icon: '⏳',
    classes: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  community_verified: {
    label: 'Community Verified',
    icon: '✓',
    classes: 'bg-green-50 text-green-700 border-green-200',
  },
  flagged: {
    label: 'Flagged · Inaccurate',
    icon: '⚠',
    classes: 'bg-red-50 text-red-700 border-red-200',
  },
};

interface TrustBadgeProps {
  trustLabel: TrustLabel;
}

export default function TrustBadge({ trustLabel }: TrustBadgeProps) {
  const c = CONFIG[trustLabel];
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full border ${c.classes}`}
      data-testid="trust-badge"
    >
      <span>{c.icon}</span>
      {c.label}
    </span>
  );
}
