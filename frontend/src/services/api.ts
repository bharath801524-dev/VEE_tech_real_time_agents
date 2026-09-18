import type { KPIData, CrisisEvent, LiveEvent, SLASummary, AnalyticsData, Client, Settings, DemoScenario, SystemHealth, AgentStatus, Alert, RSSSourceStatus } from '../types';

const BASE = 'http://localhost:8000/api';

async function get<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`API error ${r.status}: ${path}`);
  return r.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`API error ${r.status}: ${path}`);
  return r.json();
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`API error ${r.status}: ${path}`);
  return r.json();
}

async function del<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path, { method: 'DELETE' });
  if (!r.ok) throw new Error(`API error ${r.status}: ${path}`);
  return r.json();
}

export const api = {
  getKPI: () => get<KPIData>('/kpi'),
  getEvents: (params?: { limit?: number; brand?: string; source?: string; risk?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.brand) q.set('brand', params.brand);
    if (params?.source) q.set('source', params.source);
    if (params?.risk) q.set('risk', params.risk);
    return get<LiveEvent[]>(`/events?${q}`);
  },
  getEvent: (id: string) => get<LiveEvent>(`/events/${id}`),
  getCrises: () => get<CrisisEvent[]>('/crises'),
  getCrisis: (id: string) => get<CrisisEvent>(`/crises/${id}`),
  getAlerts: () => get<Alert[]>('/alerts'),
  getAnalytics: (range?: string) => get<AnalyticsData>(`/analytics?range=${range || '1h'}`),
  getSLA: () => get<SLASummary>('/sla'),
  getClients: () => get<Client[]>('/clients'),
  createClient: (client: Partial<Client>) => post<Client>('/clients', client),
  deleteClient: (id: number) => del<{ ok: boolean }>(`/clients/${id}`),
  getSettings: () => get<Settings>('/settings'),
  updateSettings: (s: Partial<Settings>) => put<Settings>('/settings', s),
  getHealth: () => get<SystemHealth>('/health'),
  getAgents: () => get<AgentStatus[]>('/agents'),
  getScenarios: () => get<DemoScenario[]>('/demo/scenarios'),
  startSimulation: (scenarioId: string) => post<{ ok: boolean; message: string }>('/demo/simulate', { scenario_id: scenarioId }),
  toggleStream: (active: boolean) => post<{ ok: boolean }>('/demo/toggle-stream', { active }),
  
  // Google News RSS & Source Controls
  getSourceStatus: () => get<RSSSourceStatus>('/ingestion/status'),
  refreshSources: () => post<{ ok: boolean; message: string; data: any }>('/ingestion/refresh'),
  setMode: (mode: 'LIVE' | 'DEMO') => post<{ ok: boolean; mode: string }>('/ingestion/mode', { mode }),
};

