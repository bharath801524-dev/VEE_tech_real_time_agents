import { useState, useEffect, useCallback, useMemo } from 'react';
import { Radio, Search, Play, Pause, RefreshCw, ExternalLink, ShieldAlert, Sparkles, Clock, Flame } from 'lucide-react';
import { api } from '../services/api';
import { wsService } from '../services/websocket';
import SourceStatusPanel from '../components/SourceStatusPanel';
import type { LiveEvent, RiskLevel, Source, Sentiment } from '../types';
import { riskBadgeClass, formatTimestamp, velocityClass, sourceIcon, sourceLabel } from '../utils';

export default function LiveFeed() {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('ALL');
  const [selectedSource, setSelectedSource] = useState<Source | 'ALL'>('ALL');
  const [selectedRisk, setSelectedRisk] = useState<RiskLevel | 'ALL'>('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState<Sentiment | 'ALL'>('ALL');
  const [brands, setBrands] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const loadInitial = useCallback(async () => {
    try {
      setLoading(true);
      const params: { limit: number; brand?: string } = { limit: 100 };
      if (selectedBrand !== 'ALL') {
        params.brand = selectedBrand;
      }
      const [fetchedEvents, clients] = await Promise.all([
        api.getEvents(params),
        api.getClients(),
      ]);
      setEvents(fetchedEvents);
      const bMap = new Map<string, string>();
      clients.forEach(c => {
        if (c.name) bMap.set(c.name.toLowerCase(), c.name);
      });
      fetchedEvents.forEach(e => {
        if (e.brand && !bMap.has(e.brand.toLowerCase())) {
          bMap.set(e.brand.toLowerCase(), e.brand);
        }
      });
      setBrands(Array.from(bMap.values()));
    } catch {
      // Backend offline fallback
    } finally {
      setLoading(false);
    }
  }, [selectedBrand]);

  useEffect(() => {
    loadInitial();

    wsService.connect();
    const unsub = wsService.on('NEW_EVENT', (msg) => {
      if (isPaused) return;
      const newEv = msg.data as LiveEvent;
      setEvents(prev => {
        // If event exists (deduplicated), update it, otherwise prepend
        const existingIdx = prev.findIndex(e => e.id === newEv.id);
        if (existingIdx !== -1) {
          const updated = [...prev];
          updated[existingIdx] = newEv;
          return updated;
        }
        return [newEv, ...prev.slice(0, 99)];
      });
    });

    const unsubTriage = wsService.on('TRIAGE_UPDATE', (msg) => {
      if (isPaused) return;
      const updatedEv = msg.data as LiveEvent;
      setEvents(prev => prev.map(e => e.id === updatedEv.id ? updatedEv : e));
    });

    const unsubMode = wsService.on('MODE_CHANGE', () => {
      loadInitial();
    });

    return () => {
      unsub();
      unsubTriage();
      unsubMode();
    };
  }, [isPaused, loadInitial]);

  const filtered = useMemo(() => {
    return events.filter(e => {
      if (selectedBrand !== 'ALL' && e.brand?.toLowerCase() !== selectedBrand.toLowerCase()) return false;
      if (selectedSource !== 'ALL' && e.source !== selectedSource) return false;
      if (selectedRisk !== 'ALL' && e.risk_level !== selectedRisk) return false;
      if (selectedSentiment !== 'ALL' && e.sentiment !== selectedSentiment) return false;
      if (search.trim()) {
        const query = search.toLowerCase();
        const inHead = e.headline?.toLowerCase().includes(query) ?? false;
        const inContent = e.content?.toLowerCase().includes(query) ?? false;
        const inBrand = e.brand?.toLowerCase().includes(query) ?? false;
        if (!inHead && !inContent && !inBrand) return false;
      }
      return true;
    });
  }, [events, selectedBrand, selectedSource, selectedRisk, selectedSentiment, search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-risk-critical/20 flex items-center justify-center">
              <Radio className="w-4 h-4 text-risk-critical animate-pulse" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Live Intelligence Feed</h1>
          </div>
          <p className="text-gray-400 text-xs mt-1">Continuous multi-source ingestion & AI pre-filtering (&lt;120s response pipeline)</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`btn-ghost flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold ${isPaused ? 'text-risk-medium border-risk-medium/30' : 'text-risk-low'}`}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
            {isPaused ? 'Resume Stream' : 'Live Streaming'}
          </button>
          <button onClick={loadInitial} className="btn-ghost p-2 text-gray-400 hover:text-white" title="Reload Feed">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Google News RSS Source Status Panel */}
      <SourceStatusPanel onRefreshCompleted={loadInitial} />

      {/* Control Filters */}
      <div className="card space-y-4">
        <div className="flex flex-col md:flex-row gap-3 items-center">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by brand, topic, headline keyword..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-surface-900 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue transition-colors"
            />
          </div>

          {/* Quick Stats in Filters */}
          <div className="flex items-center gap-2 text-xs text-gray-400 shrink-0">
            <span>Showing <strong className="text-white">{filtered.length}</strong> of {events.length}</span>
            {isPaused && (
              <span className="px-2 py-0.5 bg-risk-medium/20 text-risk-medium rounded text-[10px] font-semibold">STREAM PAUSED</span>
            )}
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-white/[0.06] text-xs">
          {/* Brand Filter */}
          <div className="flex items-center gap-1">
            <span className="text-gray-500 text-[11px] mr-1">Brand:</span>
            <select
              value={selectedBrand}
              onChange={e => setSelectedBrand(e.target.value)}
              className="bg-surface-900 border border-white/10 text-white rounded px-2 py-1 text-xs focus:outline-none"
            >
              <option value="ALL">All Brands</option>
              {brands.map(b => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>

          {/* Source Filter */}
          <div className="flex items-center gap-1">
            <span className="text-gray-500 text-[11px] mr-1">Source:</span>
            {(['ALL', 'news', 'twitter', 'reddit'] as const).map(src => (
              <button
                key={src}
                onClick={() => setSelectedSource(src)}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  selectedSource === src
                    ? 'bg-accent-blue/30 text-accent-blue font-semibold border border-accent-blue/40'
                    : 'bg-surface-900 text-gray-400 hover:text-white border border-transparent'
                }`}
              >
                {src === 'ALL' ? 'All' : `${sourceIcon(src)} ${sourceLabel(src)}`}
              </button>
            ))}
          </div>

          {/* Risk Filter */}
          <div className="flex items-center gap-1">
            <span className="text-gray-500 text-[11px] mr-1">Risk:</span>
            {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(r => (
              <button
                key={r}
                onClick={() => setSelectedRisk(r)}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  selectedRisk === r
                    ? 'bg-white/20 text-white font-semibold'
                    : 'bg-surface-900 text-gray-400 hover:text-white'
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          {/* Sentiment Filter */}
          <div className="flex items-center gap-1">
            <span className="text-gray-500 text-[11px] mr-1">Sentiment:</span>
            {(['ALL', 'Negative', 'Neutral', 'Positive'] as const).map(s => (
              <button
                key={s}
                onClick={() => setSelectedSentiment(s)}
                className={`px-2 py-1 rounded text-xs transition-colors ${
                  selectedSentiment === s
                    ? 'bg-accent-violet/30 text-accent-violet font-semibold border border-accent-violet/40'
                    : 'bg-surface-900 text-gray-400 hover:text-white border border-transparent'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Feed List */}
      <div className="space-y-3">
        {loading && events.length === 0 ? (
          <div className="card text-center py-12 text-gray-400 text-xs">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-accent-blue" />
            Loading real-time intelligence feed...
          </div>
        ) : filtered.length === 0 ? (
          <div className="card text-center py-12 text-gray-500 text-xs">
            No events match your selected filters. Try broadening your query or resuming stream.
          </div>
        ) : (
          filtered.map(e => {
            const isHighRisk = e.risk_level === 'CRITICAL' || e.risk_level === 'HIGH';
            return (
              <div
                key={e.id}
                className={`card p-4 transition-all hover:border-white/20 ${
                  e.risk_level === 'CRITICAL'
                    ? 'border-risk-critical/40 bg-risk-critical/[0.03]'
                    : e.risk_level === 'HIGH'
                    ? 'border-risk-high/30 bg-risk-high/[0.02]'
                    : ''
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <span className="text-xl mt-0.5 shrink-0" title={sourceLabel(e.source)}>
                      {sourceIcon(e.source)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1.5">
                        <span className="px-2 py-0.5 rounded bg-white/10 text-white font-semibold text-xs tracking-wide">
                          {e.brand}
                        </span>

                        {/* Source Origin Indicator */}
                        {e.source === 'reddit' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-orange-500/15 text-orange-400 border border-orange-500/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse-slow" />
                            {e.source_origin || 'Reddit'}
                          </span>
                        ) : e.source_origin?.includes('Hacker News') ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse-slow" />
                            Hacker News
                          </span>
                        ) : e.source_origin?.includes('LIVE') || e.source === 'news' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
                            LIVE • Google News RSS {e.publisher ? `(${e.publisher})` : ''}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-accent-blue/15 text-accent-blue border border-accent-blue/30">
                            DEMO • Simulated
                          </span>
                        )}

                        {e.risk_level && (
                          <span className={riskBadgeClass(e.risk_level)}>
                            {e.risk_level} {e.risk_score ? `(${e.risk_score})` : ''}
                          </span>
                        )}
                        {e.sentiment && (
                          <span className={`text-[11px] font-medium ${
                            e.sentiment === 'Negative' ? 'text-risk-critical' : e.sentiment === 'Positive' ? 'text-risk-low' : 'text-gray-400'
                          }`}>
                            {e.sentiment}
                          </span>
                        )}
                        {e.topic && (
                          <span className="text-[10px] text-gray-400 bg-surface-900 border border-white/10 px-2 py-0.5 rounded">
                            {e.topic}
                          </span>
                        )}
                        {e.velocity_ratio && e.velocity_ratio > 1.5 && (
                          <span className={`flex items-center gap-0.5 text-[10px] font-mono font-bold ${velocityClass(e.velocity_ratio)}`}>
                            <Flame className="w-3 h-3" /> {e.velocity_ratio}x velocity
                          </span>
                        )}
                        {e.mention_count && e.mention_count > 1 && (
                          <span className="text-[10px] text-accent-blue bg-accent-blue/10 px-2 py-0.5 rounded font-mono">
                            🔁 {e.mention_count} grouped mentions
                          </span>
                        )}
                      </div>

                      <h3 className="text-sm font-semibold text-white leading-snug mt-1.5">
                        {e.headline}
                      </h3>

                      {e.content && (
                        <p className="text-xs text-gray-400 mt-1.5 line-clamp-2 leading-relaxed">
                          {e.content}
                        </p>
                      )}

                      {/* AI Briefing Snapshot */}
                      {e.insight && (
                        <div className="mt-3 p-2.5 rounded-lg bg-surface-900/80 border border-white/[0.08] text-xs space-y-1">
                          <div className="flex items-center gap-1.5 font-semibold text-[11px]">
                            <Sparkles className="w-3.5 h-3.5" />
                            {e.ai_provider === 'GeminiProvider' ? (
                              <span className="text-blue-400">✨ Gemini AI 2-Minute Triage Briefing</span>
                            ) : (
                              <span className="text-accent-violet">AI 2-Minute Triage Briefing</span>
                            )}
                          </div>
                          <div className="text-gray-300"><strong className="text-gray-400">Impact:</strong> {e.insight.why_it_matters}</div>
                          <div className="text-gray-300"><strong className="text-gray-400">Action:</strong> {e.insight.recommended_action}</div>
                        </div>
                      )}

                    </div>
                  </div>

                  {/* Metadata & Actions */}
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <span className="text-[11px] text-gray-500 flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3" /> {formatTimestamp(e.timestamp)}
                    </span>
                    {e.sla_seconds && (
                      <span className="text-[10px] text-risk-low bg-risk-low/10 px-2 py-0.5 rounded-full font-mono">
                        ⏱ {Math.round(e.sla_seconds)}s SLA
                      </span>
                    )}
                    {isHighRisk && (
                      <a
                        href="/crises"
                        className="flex items-center gap-1 text-xs font-semibold text-risk-critical hover:underline mt-2"
                      >
                        <ShieldAlert className="w-3.5 h-3.5" /> Crisis Center
                      </a>
                    )}
                    {e.url && (
                      <a
                        href={e.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-accent-blue hover:text-blue-300 text-xs flex items-center gap-1 mt-1 bg-white/[0.04] hover:bg-white/[0.08] px-2 py-1 rounded transition-colors"
                      >
                        <span>{e.publisher || 'Read Article'}</span> <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
