export type Severity = 'Low' | 'Medium' | 'High';
export type ReportStatus = 'Active' | 'Resolved';
export type TrustLabel = 'ai_generated' | 'pending_verification' | 'community_verified' | 'flagged';

export interface SafetyReport {
  id: string;
  title: string;
  category: 'Local' | 'Digital';
  severity: Severity;
  summary: string;
  checklist: string[];
  status: ReportStatus;
  timestamp: string;
  isAiGenerated: boolean;
  trustLabel: TrustLabel;
  upvotes: number;
  downvotes: number;
  sourceCount: number;
  lat: number | null;
  lng: number | null;
  newsSource: string | null;
}

export interface VoteResponse {
  upvotes: number;
  downvotes: number;
  trustLabel: TrustLabel;
  userVote: 'up' | 'down' | null;
}

export interface User {
  id: string;
  username: string;
  neighborhood: string;
  role: 'User' | 'Guardian' | 'Admin';
  lat: number | null;
  lng: number | null;
}
