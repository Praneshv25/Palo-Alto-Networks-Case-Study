import axios from 'axios';
import type { SafetyReport, VoteResponse, User } from '../types/report';

const client = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('guardian_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
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

export interface CircleMessage {
  id: string;
  content: string;
  created_at: string;
  sender_id: string;
  sender_name: string;
}

export interface CircleRequest {
  id: string;
  requester_id: string;
  requester_name: string;
  status: string;
  created_at: string;
}

export async function getCircleMessages(circleOwnerId: string): Promise<CircleMessage[]> {
  const { data } = await client.get(`/circles/${circleOwnerId}/messages`);
  return data as CircleMessage[];
}

export async function sendCircleMessage(circleOwnerId: string, content: string): Promise<CircleMessage> {
  const { data } = await client.post(`/circles/${circleOwnerId}/messages`, { content });
  return data as CircleMessage;
}

export async function getCircleMembers(circleOwnerId: string): Promise<User[]> {
  const { data } = await client.get(`/circles/${circleOwnerId}/members`);
  return data as User[];
}

export async function requestJoinCircle(circleOwnerId: string): Promise<{ id: string; status: string }> {
  const { data } = await client.post(`/circles/${circleOwnerId}/request`);
  return data as { id: string; status: string };
}

export async function getCircleRequests(circleOwnerId: string): Promise<CircleRequest[]> {
  const { data } = await client.get(`/circles/${circleOwnerId}/requests`);
  return data as CircleRequest[];
}

export async function handleCircleRequest(
  circleOwnerId: string,
  requestId: string,
  status: 'approved' | 'denied'
): Promise<{ id: string; status: string }> {
  const { data } = await client.patch(`/circles/${circleOwnerId}/requests/${requestId}`, { status });
  return data as { id: string; status: string };
}
