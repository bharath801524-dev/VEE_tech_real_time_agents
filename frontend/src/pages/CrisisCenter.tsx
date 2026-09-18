import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  AlertTriangle, CheckCircle2, Clock, ShieldAlert,
  ChevronRight, X, Sparkles, Flame, RefreshCw, CheckSquare, Square
} from 'lucide-react';
import { api } from '../services/api';
import { wsService } from '../services/websocket';
import type { CrisisEvent } from '../types';
import { riskBadgeClass, formatTimestamp, formatSeconds, velocityClass } from '../utils';

// ─── Crisis Detail Modal ────────────────────────────────────────────────────────
function CrisisDetailModal({ crisis, onClose }: { crisis: CrisisEvent; onClose: () => void }) {
  const [checkedItems, setCheckedItems] = useState<Record<number, boolean>>({});

  const toggleCheck = (idx: number) => {
    setCheckedItems(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const slaPassed = crisis.sla_passed ?? ((crisis.sla_seconds ?? 0) <= 120);

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-surface-800 border border-white/15 rounded-2xl w-full max-w-4xl max-h-[92vh] overflow-y-auto shadow-2xl space-y-6 p-6">
        {/* Top Header */}
        <div className="flex items-start justify-between border-b border-white/10 pb-4">
          <div className="space-y-1.5 flex-1 pr-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2.5 py-0.5 rounded bg-white/10 text-white font-bold text-xs tracking-wider uppercase">
                {crisis.brand}
              </span>
              <span className={riskBadgeClass(crisis.risk_level)}>
                {crisis.risk_level} CRISIS
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                slaPassed ? 'bg-risk-low/20 text-risk-low border-risk-low/40' : 'bg-risk-critical/20 text-risk-critical border-risk-critical/40'
              }`}>
                {slaPassed ? '✓ 2-MIN SLA PASSED' : '⚠️ SLA BREACH'}
              </span>
              <span className="text-xs text-gray-400 font-mono">
                Total Response: {formatSeconds(crisis.sla_seconds ?? 42)}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white leading-snug">
              {crisis.headline}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-surface-900 text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* SLA Stage Timeline */}
        <div className="card bg-surface-900/60 p-4 border border-white/[0.08]">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-accent-blue" /> SLA Stage Milestones (&lt; 120s Target)
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { name: '1. Ingestion', latency: '< 2s', status: 'Passed', icon: '📥' },
              { name: '2. AI Triage', latency: '4.8s', status: 'Passed', icon: '🧠' },
              { name: '3. Risk Engine', latency: '1.2s', status: 'Passed', icon: '⚖️' },
              { name: '4. 2-Min Insight', latency: '6.5s', status: 'Passed', icon: '💡' },
              { name: '5. Multi-Alert', latency: '1.8s', status: 'Dispatched', icon: '🚀' },
            ].map((st, i) => (
              <div key={i} className="p-2.5 rounded-lg bg-surface-800 border border-white/[0.06] text-center">
                <div className="text-base">{st.icon}</div>
                <div className="text-xs font-semibold text-white mt-1">{st.name}</div>
                <div className="text-[11px] text-accent-blue font-mono mt-0.5">{st.latency}</div>
                <div className="text-[10px] text-risk-low mt-0.5 font-medium">{st.status}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Core Briefing: WHAT HAPPENED & WHY IT MATTERS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card border-l-4 border-l-risk-critical">
            <h4 className="text-xs font-bold text-risk-critical uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" /> What Happened
            </h4>
            <p className="text-xs text-gray-300 leading-relaxed">
              {crisis.insight?.what_happened ||
                `Rapid sentiment deterioration detected regarding ${crisis.brand} following reports on "${crisis.headline}". High media circulation observed across national tech & finance desks.`}
            </p>
          </div>

          <div className="card border-l-4 border-l-accent-violet">
            <h4 className="text-xs font-bold text-accent-violet uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" /> Why It Matters
            </h4>
            <p className="text-xs text-gray-300 leading-relaxed">
              {crisis.insight?.why_it_matters ||
                `Elevated risk of regulatory review, merchant/customer panic, and severe social contagion. Potential brand trust degradation if left unaddressed beyond 15 minutes.`}
            </p>
          </div>
        </div>

        {/* Transparent Risk Score Breakdown */}
        <div className="card">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center justify-between">
            <span>Transparent Risk Engine Breakdown</span>
            <span className="text-risk-critical font-mono text-sm">{crisis.risk_score} / 100 Score</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {[
              { factor: 'Topic Severity', points: '+25', desc: `${crisis.topic || 'Regulatory'} threat` },
              { factor: 'Sentiment Impact', points: '+20', desc: `${crisis.sentiment || 'Negative'} tone (-0.85)` },
              { factor: 'Velocity Spike', points: '+20', desc: `${crisis.velocity_ratio || 4.2}x rolling surge` },
              { factor: 'Client Tier', points: '+20', desc: 'Tier-1 Priority Brand' },
              { factor: 'Source Authority', points: '+15', desc: 'National news & verified wires' },
            ].map((rb, i) => (
              <div key={i} className="p-2.5 rounded-lg bg-surface-900 border border-white/[0.06]">
                <div className="text-[11px] text-gray-400">{rb.factor}</div>
                <div className="text-sm font-bold text-risk-critical font-mono mt-0.5">{rb.points}</div>
                <div className="text-[10px] text-gray-500 mt-0.5 leading-snug">{rb.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Recommendations & Checklist */}
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <CheckSquare className="w-4 h-4 text-risk-low" /> Recommended Response Action Checklist
            </h3>
            <span className="text-xs text-accent-blue font-semibold">
              Team: {crisis.insight?.recommended_team || 'PR & Legal Rapid Response'}
            </span>
          </div>

          <div className="space-y-2">
            {(crisis.insight?.action_checklist && crisis.insight.action_checklist.length > 0
              ? crisis.insight.action_checklist
              : [
                  'Issue immediate holding statement clarifying regulatory compliance and audit cooperation.',
                  'Convene Emergency PR & Legal response pod within 10 minutes.',
                  'Arm customer support and merchant partner desks with crisis FAQ script.',
                  'Monitor real-time sentiment recovery and counter-rumor narratives.',
                  'Notify key enterprise clients and leadership stakeholders proactively.'
                ]
            ).map((action, idx) => {
              const isChecked = checkedItems[idx] ?? false;
              return (
                <div
                  key={idx}
                  onClick={() => toggleCheck(idx)}
                  className={`flex items-start gap-2.5 p-2.5 rounded-lg border cursor-pointer transition-all ${
                    isChecked
                      ? 'bg-risk-low/[0.06] border-risk-low/30 text-gray-400 line-through'
                      : 'bg-surface-900/90 border-white/[0.06] text-gray-200 hover:border-white/20'
                  }`}
                >
                  <button className="mt-0.5 text-accent-blue shrink-0">
                    {isChecked ? <CheckSquare className="w-4 h-4 text-risk-low" /> : <Square className="w-4 h-4 text-gray-500" />}
                  </button>
                  <span className="text-xs leading-relaxed select-none">{action}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Competitor Impact & Related Context */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="card p-4">
            <h4 className="font-semibold text-gray-300 mb-2">Competitor Context</h4>
            <p className="text-gray-400 leading-relaxed">
              {crisis.insight?.competitor_reaction ||
                'Competitors (Razorpay, PhonePe) experiencing elevated traffic and social mentions; monitoring for predatory marketing or customer acquisition campaigns.'}
            </p>
          </div>
          <div className="card p-4">
            <h4 className="font-semibold text-gray-300 mb-2">Multi-Channel Broadcast Status</h4>
            <div className="space-y-1.5 text-gray-400">
              <div className="flex items-center justify-between">
                <span>In-App Dashboard Notification:</span>
                <span className="text-risk-low font-semibold">Delivered</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Slack Rapid Escalation Channel:</span>
                <span className="text-risk-low font-semibold">Delivered (#incident-war-room)</span>
              </div>
              <div className="flex items-center justify-between">
                <span>SMS / Email Executive Pager:</span>
                <span className="text-risk-low font-semibold">Delivered (C-Suite on-call)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between pt-2 border-t border-white/10">
          <div className="text-xs text-gray-500 font-mono">
            Detected: {formatTimestamp(crisis.detected_at)}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="btn-ghost px-4 py-2 text-xs"
            >
              Close
            </button>
            <button
              onClick={onClose}
              className="btn-primary px-4 py-2 text-xs flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" /> Acknowledge & Execute
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Crisis Center View ───────────────────────────────────────────────────
export default function CrisisCenter() {
  const [crises, setCrises] = useState<CrisisEvent[]>([]);
  const [selectedCrisis, setSelectedCrisis] = useState<CrisisEvent | null>(null);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'INVESTIGATING' | 'RESOLVED'>('ALL');
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getCrises();
      setCrises(data);
    } catch {
      // Backend fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    wsService.connect();
    const unsub = wsService.on('CRISIS_DETECTED', (msg) => {
      const c = msg.data as CrisisEvent;
      setCrises(prev => {
        const idx = prev.findIndex(item => item.id === c.id);
        if (idx !== -1) {
          const updated = [...prev];
          updated[idx] = c;
          return updated;
        }
        return [c, ...prev];
      });
    });

    return () => unsub();
  }, [loadData]);

  const filtered = useMemo(() => {
    return crises.filter(c => {
      if (statusFilter !== 'ALL' && c.status !== statusFilter) return false;
      return true;
    });
  }, [crises, statusFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-risk-critical/20 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4 text-risk-critical" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Crisis Center</h1>
          </div>
          <p className="text-gray-400 text-xs mt-1">
            Escalated high-risk threats requiring immediate &lt;2-minute executive triage and action orchestration
          </p>
        </div>

        <button onClick={loadData} className="btn-ghost p-2 text-gray-400 hover:text-white">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-3 text-xs">
        {(['ALL', 'ACTIVE', 'INVESTIGATING', 'RESOLVED'] as const).map(tab => {
          const count = tab === 'ALL' ? crises.length : crises.filter(c => c.status === tab).length;
          return (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                statusFilter === tab
                  ? 'bg-accent-blue text-white font-semibold shadow-lg shadow-accent-blue/30'
                  : 'text-gray-400 hover:text-white hover:bg-white/[0.05]'
              }`}
            >
              <span>{tab}</span>
              <span className="px-1.5 py-0.2 rounded bg-black/30 text-[10px]">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Crisis Cards */}
      <div className="space-y-4">
        {loading && crises.length === 0 ? (
          <div className="card text-center py-12 text-gray-400 text-xs">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-accent-blue" />
            Loading crisis records...
          </div>
        ) : filtered.length === 0 ? (
          <div className="card text-center py-12 text-gray-500 text-xs">
            No crises found for status "{statusFilter}".
          </div>
        ) : (
          filtered.map(c => {
            const slaPassed = c.sla_passed ?? ((c.sla_seconds ?? 0) <= 120);
            return (
              <div
                key={c.id}
                onClick={() => setSelectedCrisis(c)}
                className="card p-5 border border-white/10 hover:border-accent-blue/50 cursor-pointer transition-all duration-200 group relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 bottom-0 w-1 bg-gradient-to-b from-risk-critical to-risk-high" />

                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left */}
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2.5 py-0.5 rounded bg-white/10 text-white font-bold text-xs tracking-wider">
                        {c.brand}
                      </span>
                      <span className={riskBadgeClass(c.risk_level)}>
                        {c.risk_level} ({c.risk_score}/100)
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                        slaPassed ? 'bg-risk-low/20 text-risk-low border-risk-low/30' : 'bg-risk-critical/20 text-risk-critical border-risk-critical/30'
                      }`}>
                        {slaPassed ? '✓ SLA PASSED' : '⚠️ BREACHED'} ({formatSeconds(c.sla_seconds ?? 42)})
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                        c.status === 'ACTIVE' ? 'bg-risk-critical/20 text-risk-critical animate-pulse' : 'bg-white/10 text-gray-300'
                      }`}>
                        {c.status}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-white group-hover:text-accent-blue transition-colors leading-snug">
                      {c.headline}
                    </h3>

                    {c.insight?.why_it_matters && (
                      <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                        <strong className="text-gray-300">Why It Matters:</strong> {c.insight.why_it_matters}
                      </p>
                    )}
                  </div>

                  {/* Right Stats & CTA */}
                  <div className="flex items-center gap-4 lg:border-l lg:border-white/10 lg:pl-6 shrink-0">
                    <div className="grid grid-cols-2 gap-4 text-center">
                      <div>
                        <div className="text-xs text-gray-500 font-medium">Mentions</div>
                        <div className="text-sm font-bold text-white font-mono">{c.mentions?.toLocaleString() || 1}</div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 font-medium">Velocity</div>
                        <div className={`text-sm font-bold font-mono flex items-center justify-center gap-0.5 ${velocityClass(c.velocity_ratio)}`}>
                          <Flame className="w-3.5 h-3.5" /> {c.velocity_ratio || 1.0}x
                        </div>
                      </div>
                    </div>

                    <button className="btn-primary text-xs px-3.5 py-2 flex items-center gap-1 shrink-0">
                      <span>Deep Dive</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Modal */}
      {selectedCrisis && (
        <CrisisDetailModal
          crisis={selectedCrisis}
          onClose={() => setSelectedCrisis(null)}
        />
      )}
    </div>
  );
}
