import { useState, useEffect, useCallback, type ElementType } from 'react';
import {
  AlertTriangle, TrendingUp, Shield, Clock, Zap, Activity,
  Play, BarChart2, RefreshCw
} from 'lucide-react';
import { api } from '../services/api';
import { wsService } from '../services/websocket';
import SourceStatusPanel from '../components/SourceStatusPanel';
import type { KPIData, LiveEvent, CrisisEvent, SystemHealth, AgentStatus, DemoScenario } from '../types';
import { riskBadgeClass, formatTimestamp, formatNumber, velocityClass, sourceIcon } from '../utils';

// ─── KPI Card ────────────────────────────────────────────────────────────────
function KPICard({ label, value, sub, color, icon: Icon }: {
  label: string; value: string | number; sub?: string; color: string; icon: ElementType;
}) {
  return (
    <div className="card-hover group">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color} bg-opacity-20`}>
          <Icon className={`w-4.5 h-4.5 ${color}`} />
        </div>
        <div className="text-xs text-gray-500 font-medium">{sub}</div>
      </div>
      <div className="text-2xl font-bold text-white tracking-tight">{formatNumber(typeof value === 'number' ? value : undefined) || value}</div>
      <div className="text-xs text-gray-400 mt-1 font-medium">{label}</div>
    </div>
  );
}

// ─── Comparison Table ─────────────────────────────────────────────────────────
function ComparisonTable() {
  const rows = [
    ['Response Time', '5–6 Hours', '<2 Minutes'],
    ['Processing', 'Batch', 'Real-time Streaming'],
    ['Analysis', 'Manual Analyst', 'AI Agents'],
    ['Alerting', 'Keyword Match', 'Context-Aware Risk'],
    ['Delivery', 'Email Reports', 'Instant Multi-Channel'],
    ['Escalation', 'Human Chain', 'Automated Rules'],
    ['SLA Visibility', 'None', 'Real-time Monitoring'],
  ];
  return (
    <div className="card">
      <h3 className="font-bold text-white mb-4 flex items-center gap-2">
        <Zap className="w-4 h-4 text-accent-blue" /> MindMesh vs Traditional
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-2 text-gray-500 font-medium">Capability</th>
              <th className="text-left py-2 text-gray-500 font-medium">Traditional</th>
              <th className="text-left py-2 text-risk-low font-semibold">MindMesh</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([cap, old, neu], i) => (
              <tr key={i} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                <td className="py-2 text-gray-400">{cap}</td>
                <td className="py-2 text-risk-high">{old}</td>
                <td className="py-2 text-risk-low font-medium">{neu}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── System Health ─────────────────────────────────────────────────────────────
function SystemHealthPanel({ health }: { health: SystemHealth | null }) {
  const services = [
    { label: 'Ingestion', key: 'ingestion' },
    { label: 'Queue', key: 'queue' },
    { label: 'AI Agent', key: 'ai_agent' },
    { label: 'Risk Engine', key: 'risk_engine' },
    { label: 'Alert Engine', key: 'alert_engine' },
    { label: 'Database', key: 'database' },
    { label: 'WebSocket', key: 'websocket' },
  ] as const;

  return (
    <div className="card">
      <h3 className="font-bold text-white mb-4 flex items-center gap-2">
        <Activity className="w-4 h-4 text-accent-cyan" /> System Health
      </h3>
      <div className="grid grid-cols-2 gap-2 mb-4">
        {services.map(({ label, key }) => (
          <div key={key} className="flex items-center gap-2 py-1">
            <div className={health?.[key] ? 'status-dot-green' : 'status-dot-red'} />
            <span className="text-xs text-gray-300">{label}</span>
          </div>
        ))}
      </div>
      {health && (
        <div className="grid grid-cols-3 gap-2 border-t border-white/10 pt-3">
          <div className="text-center">
            <div className="text-risk-low font-bold text-sm">{health.events_per_sec}/s</div>
            <div className="text-[10px] text-gray-500">Events</div>
          </div>
          <div className="text-center">
            <div className="text-accent-blue font-bold text-sm">{health.queue_depth}</div>
            <div className="text-[10px] text-gray-500">Queue</div>
          </div>
          <div className="text-center">
            <div className="text-accent-violet font-bold text-sm">{health.ai_processing_ms}ms</div>
            <div className="text-[10px] text-gray-500">AI Avg</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Agent Status ──────────────────────────────────────────────────────────────
function AgentPanel({ agents }: { agents: AgentStatus[] }) {
  return (
    <div className="card">
      <h3 className="font-bold text-white mb-4 flex items-center gap-2">
        <Shield className="w-4 h-4 text-accent-violet" /> AI Agents
      </h3>
      <div className="space-y-3">
        {agents.map((a) => (
          <div key={a.name} className="flex items-center gap-3">
            <div className={a.active ? 'status-dot-green' : 'status-dot-red'} />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-gray-200 truncate">{a.name}</div>
              <div className="text-[10px] text-gray-500">{a.processed_today} processed · {a.avg_processing_ms}ms avg</div>
            </div>
            <span className="text-[10px] text-risk-low font-semibold">{a.active ? 'ACTIVE' : 'OFFLINE'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Demo Simulation ──────────────────────────────────────────────────────────
function DemoSimulation({ scenarios }: { scenarios: DemoScenario[] }) {
  const [loading, setLoading] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<string | null>(null);

  const run = async (id: string) => {
    setLoading(id);
    try {
      const res = await api.startSimulation(id);
      setLastResult(res.message);
    } catch {
      setLastResult('Simulation error. Backend may be unavailable.');
    } finally {
      setLoading(null);
    }
  };

  const riskColors: Record<string, string> = {
    CRITICAL: 'border-risk-critical/40 bg-risk-critical/5',
    HIGH: 'border-risk-high/40 bg-risk-high/5',
    LOW: 'border-risk-low/40 bg-risk-low/5',
  };

  return (
    <div className="card">
      <h3 className="font-bold text-white mb-1 flex items-center gap-2">
        <Play className="w-4 h-4 text-risk-critical" /> Crisis Simulation
      </h3>
      <p className="text-xs text-gray-500 mb-4">Trigger a realistic crisis scenario and watch the AI pipeline respond in real-time.</p>
      <div className="space-y-3">
        {scenarios.map((s) => (
          <div key={s.id} className={`border rounded-lg p-3 ${riskColors[s.expected_risk] || 'border-white/10'}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="text-sm font-semibold text-white">{s.name}</div>
                <div className="text-xs text-gray-400 mt-0.5">{s.description}</div>
                <div className="flex gap-2 mt-1.5">
                  <span className={riskBadgeClass(s.expected_risk)}>{s.expected_risk}</span>
                  <span className="text-[10px] text-gray-500 bg-white/5 rounded-full px-2 py-0.5">{s.expected_topic}</span>
                </div>
              </div>
              <button
                onClick={() => run(s.id)}
                disabled={loading === s.id}
                className="btn-danger text-xs px-3 py-1.5 shrink-0 disabled:opacity-50"
              >
                {loading === s.id ? 'Running...' : 'RUN'}
              </button>
            </div>
          </div>
        ))}
      </div>
      {lastResult && (
        <div className="mt-3 p-3 bg-risk-low/10 border border-risk-low/30 rounded-lg text-xs text-risk-low">
          {lastResult}
        </div>
      )}
    </div>
  );
}

// ─── Recent Events Strip ──────────────────────────────────────────────────────
function RecentEventStrip({ events }: { events: LiveEvent[] }) {
  return (
    <div className="card">
      <h3 className="font-bold text-white mb-3 flex items-center gap-2">
        <TrendingUp className="w-4 h-4 text-accent-blue" /> Recent Intelligence Events
        <span className="ml-auto text-xs text-gray-500 font-normal">Last 10</span>
      </h3>
      <div className="space-y-2 max-h-80 overflow-y-auto scrollbar-thin">
        {events.slice(0, 10).map((e) => {
          const isLive = e.source_origin?.includes('LIVE') || e.source === 'news';
          return (
            <div key={e.id} className="flex items-start gap-3 p-2.5 rounded-lg bg-surface-900/50 hover:bg-white/[0.04] border border-white/[0.04] transition-colors">
              <div className="text-base leading-none mt-0.5">{sourceIcon(e.source)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-[10px] font-semibold text-white bg-white/10 px-1.5 py-0.5 rounded">{e.brand}</span>
                  {isLive ? (
                    <span className="text-[9px] font-semibold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-1.5 py-0.5 rounded">
                      LIVE • {e.publisher || 'Google News'}
                    </span>
                  ) : (
                    <span className="text-[9px] font-semibold text-accent-blue bg-accent-blue/15 border border-accent-blue/30 px-1.5 py-0.5 rounded">
                      DEMO • Simulated
                    </span>
                  )}
                  {e.risk_level && (
                    <span className={`text-[10px] font-semibold ${e.risk_level === 'CRITICAL' ? 'text-risk-critical' : e.risk_level === 'HIGH' ? 'text-risk-high' : 'text-gray-400'}`}>
                      {e.risk_level} {e.risk_score ? `(${e.risk_score})` : ''}
                    </span>
                  )}
                  {e.velocity_ratio && e.velocity_ratio > 1.5 && (
                    <span className={`text-[10px] font-mono ${velocityClass(e.velocity_ratio)}`}>{e.velocity_ratio}x</span>
                  )}
                  <span className="text-[10px] text-gray-500 ml-auto font-mono">{formatTimestamp(e.timestamp)}</span>
                </div>
                <div className="text-xs text-white leading-snug truncate font-medium">{e.headline}</div>
                {e.url && (
                  <a
                    href={e.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] text-accent-cyan hover:underline inline-block mt-1"
                  >
                    ↗ Open Original Article
                  </a>
                )}
              </div>
            </div>
          );
        })}
        {events.length === 0 && (
          <p className="text-xs text-gray-500 text-center py-4">Waiting for events from the live stream...</p>
        )}
      </div>
    </div>
  );
}

// ─── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [kpi, setKpi] = useState<KPIData | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [activeCrisis, setActiveCrisis] = useState<CrisisEvent | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [k, h, a, s, ev] = await Promise.all([
        api.getKPI(),
        api.getHealth(),
        api.getAgents(),
        api.getScenarios(),
        api.getEvents({ limit: 20 }),
      ]);
      setKpi(k); setHealth(h); setAgents(a); setScenarios(s); setEvents(ev);
    } catch { /* backend offline */ }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);

    wsService.connect();
    const unsub1 = wsService.on('NEW_EVENT', (msg) => {
      const ev = msg.data as LiveEvent;
      setEvents(prev => [ev, ...prev.slice(0, 29)]);
    });
    const unsub2 = wsService.on('CRISIS_DETECTED', (msg) => {
      setActiveCrisis(msg.data as CrisisEvent);
    });
    const unsub3 = wsService.on('KPI_UPDATE', () => loadData());

    return () => { clearInterval(interval); unsub1(); unsub2(); unsub3(); };
  }, [loadData]);

  const kpiCards = [
    { label: 'Critical Alerts', value: kpi?.critical_alerts ?? 0, sub: 'Today', color: 'text-risk-critical', icon: AlertTriangle },
    { label: 'High-Risk Events', value: kpi?.high_risk_events ?? 0, sub: 'Today', color: 'text-risk-high', icon: Shield },
    { label: 'Articles Monitored', value: kpi?.articles_monitored ?? 0, sub: '24/7', color: 'text-accent-blue', icon: BarChart2 },
    { label: 'Avg Response Time', value: kpi ? `${kpi.avg_response_time_sec}s` : '—', sub: 'Target <120s', color: 'text-accent-violet', icon: Clock },
    { label: 'SLA Compliance', value: kpi ? `${kpi.sla_compliance_pct}%` : '—', sub: 'Target 100%', color: 'text-risk-low', icon: Activity },
    { label: 'Missed Critical', value: kpi ? `${kpi.missed_critical_pct}%` : '—', sub: 'Target 0%', color: 'text-risk-medium', icon: Zap },
  ];

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">
            <span className="text-gradient">MindMesh</span> Dashboard
          </h1>
          <p className="text-gray-400 text-sm mt-1">AI Agents & Real-Time Intelligence — Media Crisis Response</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-risk-low/10 border border-risk-low/30 rounded-full">
            <div className="status-dot-green" />
            <span className="text-xs text-risk-low font-semibold">SYSTEM ONLINE</span>
          </div>
          <button onClick={loadData} className="btn-ghost p-2">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Crisis Banner */}
      {activeCrisis && (
        <div className="crisis-banner flex items-start gap-3">
          <div className="status-dot-red mt-1.5" />
          <div className="flex-1">
            <div className="text-risk-critical font-bold text-sm">ACTIVE CRISIS — {activeCrisis.brand}</div>
            <div className="text-gray-300 text-sm mt-1">{activeCrisis.headline}</div>
            <div className="flex gap-3 mt-2">
              <span className={riskBadgeClass(activeCrisis.risk_level)}>{activeCrisis.risk_level}</span>
              <span className="text-xs text-gray-400">Risk {activeCrisis.risk_score}/100</span>
            </div>
          </div>
          <button onClick={() => setActiveCrisis(null)} className="text-gray-500 hover:text-white">✕</button>
        </div>
      )}

      {/* Google News RSS Source Status Panel */}
      <SourceStatusPanel onRefreshCompleted={loadData} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpiCards.map((card) => (
          <KPICard key={card.label} {...card} />
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="xl:col-span-2 space-y-6">
          <DemoSimulation scenarios={scenarios} />
          <ComparisonTable />
          <RecentEventStrip events={events} />
        </div>

        {/* Right column */}
        <div className="space-y-6">
          <SystemHealthPanel health={health} />
          <AgentPanel agents={agents} />
        </div>
      </div>
    </div>
  );
}
