// Shared types for MindMesh platform

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Sentiment = 'Positive' | 'Neutral' | 'Negative';
export type Urgency = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Source = 'news' | 'twitter' | 'reddit';
export type VelocityStatus = 'NORMAL' | 'ELEVATED' | 'SPIKE' | 'CRITICAL SPIKE';
export type AlertChannel = 'in_app' | 'slack' | 'email' | 'sms';
export type SystemMode = 'DEMO' | 'LIVE';

export interface LiveEvent {
  id: string;
  source: Source;
  source_origin?: string;
  publisher?: string;
  timestamp: number;
  brand: string;
  headline: string;
  content: string;
  url?: string;
  location?: string;
  sentiment?: Sentiment;
  risk_level?: RiskLevel;
  risk_score?: number;
  topic?: string;
  velocity_ratio?: number;
  velocity_status?: VelocityStatus;
  confidence?: number;
  mention_count?: number;
  sla_seconds?: number;
  ai_provider?: string;  // 'GeminiProvider' | 'DemoAIProvider'
  ai_analysis?: AIAnalysis;
  insight?: CrisisInsight;
}

export interface RSSSourceStatus {
  source_name: string;
  status: 'CONNECTED' | 'FAILED' | 'IDLE' | 'INITIALIZING';
  is_running: boolean;
  current_mode: SystemMode;
  last_successful_fetch: number | null;
  last_fetch_attempt: number | null;
  articles_fetched_total: number;
  articles_ingested_total: number;
  last_article_published: number | null;
  last_error: string | null;
  poll_interval_seconds: number;
  monitored_queries: string[];
}

export interface AIAnalysis {
  client: string;
  client_tier: string;
  topic: string;
  sentiment: Sentiment;
  sentiment_score: number;
  risk_level: RiskLevel;
  risk_score: number;
  competitor_impact: string;
  urgency: Urgency;
  confidence: number;
}

export interface RiskBreakdown {
  label: string;
  score: number;
  description: string;
}

export interface CrisisInsight {
  what_happened: string;
  why_it_matters: string;
  recommended_action: string;
  priority: string;
  recommended_team: string;
  action_checklist: string[];
  competitor_reaction?: string;
}

export interface CrisisEvent {
  id: string;
  event_id: string;
  brand: string;
  headline: string;
  topic: string;
  risk_score: number;
  risk_level: RiskLevel;
  mentions: number;
  velocity_ratio: number;
  sentiment: Sentiment;
  status: 'ACTIVE' | 'INVESTIGATING' | 'RESOLVED';
  detected_at: number;
  sla_passed?: boolean;
  sla_seconds?: number;
  event?: LiveEvent;
  insight?: CrisisInsight;
  risk_breakdown?: RiskBreakdown[];
  sla_stages?: SLAStage[];
  related_coverage?: RelatedItem[];
  competitor_reactions?: RelatedItem[];
}

export interface SLAStage {
  label: string;
  timestamp: number;
  latency_seconds: number;
  icon: string;
}

export interface SLAMetric {
  event_id: string;
  crisis_id?: string;
  ingest_timestamp: number;
  triage_timestamp: number;
  risk_timestamp: number;
  insight_timestamp: number;
  alert_timestamp: number;
  total_latency_seconds: number;
  triage_latency_seconds: number;
  risk_latency_seconds: number;
  insight_latency_seconds: number;
  alert_latency_seconds: number;
  sla_passed: boolean;
  target_seconds: number;
  brand?: string;
  headline?: string;
}

export interface Alert {
  id: string;
  crisis_id?: string;
  event_id: string;
  channel: AlertChannel;
  alert_level: RiskLevel;
  sent_at: number;
  status: string;
  brand?: string;
  headline?: string;
  risk_score?: number;
}

export interface KPIData {
  critical_alerts: number;
  high_risk_events: number;
  articles_monitored: number;
  avg_response_time_sec: number;
  sla_compliance_pct: number;
  missed_critical_pct: number;
  events_per_sec: number;
  queue_depth: number;
  mode: SystemMode;
}

export interface SLASummary {
  compliance_pct: number;
  avg_seconds: number;
  p50_seconds: number;
  p95_seconds: number;
  p99_seconds: number;
  total_events: number;
  total_breaches: number;
  critical_breaches: number;
  target_seconds: number;
  recent_events: SLAMetric[];
}

export interface AnalyticsData {
  mentions_over_time: { time: string; news: number; twitter: number; reddit: number; total: number }[];
  sentiment_distribution: { Positive: number; Neutral: number; Negative: number };
  risk_distribution: { LOW: number; MEDIUM: number; HIGH: number; CRITICAL: number };
  source_distribution: { news: number; twitter: number; reddit: number };
  top_topics: { topic: string; count: number }[];
  velocity_spikes: { time: string; velocity: number; baseline: number }[];
  geo_mentions: { city: string; count: number; lat: number; lng: number }[];
}

export interface Client {
  id: number;
  name: string;
  tier: string;
  keywords: string[];
  competitors: string[];
  is_active: boolean;
}

export interface SystemHealth {
  ingestion: boolean;
  queue: boolean;
  ai_agent: boolean;
  risk_engine: boolean;
  alert_engine: boolean;
  database: boolean;
  websocket: boolean;
  events_per_sec: number;
  queue_depth: number;
  ai_processing_ms: number;
}

export interface AgentStatus {
  name: string;
  active: boolean;
  processed_today: number;
  avg_processing_ms: number;
  errors: number;
}

// WebSocket message types
export type WSMessageType =
  | 'NEW_EVENT'
  | 'TRIAGE_UPDATE'
  | 'RISK_UPDATE'
  | 'CRISIS_DETECTED'
  | 'ALERT_TRIGGERED'
  | 'SLA_UPDATE'
  | 'KPI_UPDATE'
  | 'HEALTH_UPDATE'
  | 'DEMO_STEP'
  | 'MODE_CHANGE'
  | 'CONNECTED';

export interface WSMessage {
  type: WSMessageType;
  data: unknown;
  timestamp: number;
}

export interface RelatedItem {
  source: string;
  headline: string;
  url?: string;
  timestamp: number;
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  expected_risk: RiskLevel;
  expected_topic: string;
  client: string;
}

export interface Settings {
  mode: SystemMode;
  risk_threshold: number;
  critical_threshold: number;
  cooldown_seconds: number;
  alerts_in_app: boolean;
  alerts_slack: boolean;
  alerts_email: boolean;
  alerts_sms: boolean;
  sla_target_seconds: number;
}
