import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ReportCard from '../src/components/ReportCard';
import type { SafetyReport } from '../src/types/report';

vi.mock('../src/lib/api', () => ({
  updateReport: vi.fn(),
  voteOnReport: vi.fn(),
}));

function makeReport(overrides: Partial<SafetyReport> = {}): SafetyReport {
  return {
    id: 'rep_test',
    title: 'Test Fire Report',
    category: 'Local',
    severity: 'High',
    summary: 'A fire has been reported near the park.',
    checklist: ['Stay away.', 'Call 911.', 'Check alerts.'],
    status: 'Active',
    timestamp: new Date().toISOString(),
    isAiGenerated: true,
    trustLabel: 'ai_generated',
    upvotes: 2,
    downvotes: 0,
    ...overrides,
  };
}

describe('ReportCard', () => {
  it('renders title and summary', () => {
    render(
      <ReportCard report={makeReport()} userId="user_001" onUpdate={() => {}} />
    );
    expect(screen.getByText('Test Fire Report')).toBeInTheDocument();
    expect(screen.getByText(/fire has been reported/)).toBeInTheDocument();
  });

  it('shows correct severity badge for High', () => {
    render(
      <ReportCard report={makeReport({ severity: 'High' })} userId="user_001" onUpdate={() => {}} />
    );
    const badge = screen.getByTestId('severity-badge');
    expect(badge).toHaveTextContent('High');
  });

  it('shows correct severity badge for Low', () => {
    render(
      <ReportCard report={makeReport({ severity: 'Low' })} userId="user_001" onUpdate={() => {}} />
    );
    const badge = screen.getByTestId('severity-badge');
    expect(badge).toHaveTextContent('Low');
  });

  it('shows "AI Generated" trust badge when isAiGenerated is true', () => {
    render(
      <ReportCard
        report={makeReport({ isAiGenerated: true, trustLabel: 'ai_generated' })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    const trustBadge = screen.getByTestId('trust-badge');
    expect(trustBadge).toHaveTextContent('AI Generated');
  });

  it('shows "Pending Verification" badge for fallback reports', () => {
    render(
      <ReportCard
        report={makeReport({ isAiGenerated: false, trustLabel: 'pending_verification' })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    const trustBadge = screen.getByTestId('trust-badge');
    expect(trustBadge).toHaveTextContent('Pending Verification');
  });

  it('shows "Community Verified" badge', () => {
    render(
      <ReportCard
        report={makeReport({ trustLabel: 'community_verified', upvotes: 5 })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    const trustBadge = screen.getByTestId('trust-badge');
    expect(trustBadge).toHaveTextContent('Community Verified');
  });

  it('shows "Flagged" badge for inaccurate reports', () => {
    render(
      <ReportCard
        report={makeReport({ trustLabel: 'flagged', downvotes: 4 })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    const trustBadge = screen.getByTestId('trust-badge');
    expect(trustBadge).toHaveTextContent('Flagged');
  });

  it('renders with reduced opacity when flagged', () => {
    const { container } = render(
      <ReportCard
        report={makeReport({ trustLabel: 'flagged' })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    const card = container.querySelector('[data-testid="report-card"]');
    expect(card?.className).toContain('opacity-50');
  });

  it('shows vote counts', () => {
    render(
      <ReportCard
        report={makeReport({ upvotes: 7, downvotes: 2 })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows "Resolved" pill when status is Resolved', () => {
    render(
      <ReportCard
        report={makeReport({ status: 'Resolved' })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    expect(screen.getByText('Resolved')).toBeInTheDocument();
  });

  it('hides "Mark Resolved" button when already resolved', () => {
    render(
      <ReportCard
        report={makeReport({ status: 'Resolved' })}
        userId="user_001"
        onUpdate={() => {}}
      />
    );
    expect(screen.queryByText('Mark Resolved')).not.toBeInTheDocument();
  });
});
