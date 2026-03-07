import axios from 'axios';
import type { SafetyReport, VoteResponse, User } from '../types/report';

const client = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
});


function mapReport(raw: Record<string, unknown>): SafetyReport {
  const cat = raw.category as string;
  return {
    id: raw.id as string,
    title: raw.title as string,
    category: cat === 'Local_Physical' ? 'Local' : 'Digital',
    severity: raw.severity as SafetyReport['severity'],
    summary: raw.summary as string,
    checklist: raw.checklist as string[],
    status: raw.status as SafetyReport['status'],
    timestamp: (raw.created_at as string) || '',
    isAiGenerated: Boolean(raw.is_ai_generated),
    trustLabel: raw.trust_label as SafetyReport['trustLabel'],
    upvotes: raw.upvotes as number,
    downvotes: raw.downvotes as number,
  };
}

export async function getReports(params?: {
  category?: string;
  search?: string;
  status?: string;
  severity?: string;
}): Promise<SafetyReport[]> {
  const { data } = await client.get('/reports', { params });
  return (data as Record<string, unknown>[]).map(mapReport);
}

export async function createReport(body: {
  content: string;
  category: string;
  author_id: string;
}): Promise<SafetyReport> {
  const { data } = await client.post('/reports', body);
  return mapReport(data as Record<string, unknown>);
}

export async function updateReport(
  id: string,
  body: { status: string; resolution_note?: string }
): Promise<SafetyReport> {
  const { data } = await client.patch(`/reports/${id}`, body);
  return mapReport(data as Record<string, unknown>);
}

export async function voteOnReport(
  reportId: string,
  body: { user_id: string; vote_type: 'up' | 'down' }
): Promise<VoteResponse> {
  const { data } = await client.post(`/reports/${reportId}/vote`, body);
  const raw = data as Record<string, unknown>;
  return {
    upvotes: raw.upvotes as number,
    downvotes: raw.downvotes as number,
    trustLabel: raw.trust_label as VoteResponse['trustLabel'],
    userVote: (raw.user_vote as VoteResponse['userVote']) || null,
  };
}

export async function getUsers(): Promise<User[]> {
  const { data } = await client.get('/users');
  return data as User[];
}

export async function healthCheck(): Promise<{ status: string; ai_service: string }> {
  const { data } = await client.get('/health');
  return data as { status: string; ai_service: string };
}
