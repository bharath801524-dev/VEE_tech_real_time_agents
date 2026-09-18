import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Globe, AlertCircle, CheckCircle2, Sparkles, Layers } from 'lucide-react';
import { api } from '../services/api';
import { wsService } from '../services/websocket';
import type { RSSSourceStatus, SystemMode } from '../types';
import { formatTimestamp } from '../utils';

interface Props {
  onRefreshCompleted?: () => void;
}

export default function SourceStatusPanel({ onRefreshCompleted }: Props) {
  const [status, setStatus] = useState<RSSSourceStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [switchingMode, setSwitchingMode] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      const data = await api.getSourceStatus();
      setStatus(data);
    } catch {
      // Backend offline
    }
  }, []);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 8000);

    const unsub = wsService.on('MODE_CHANGE', () => {
      loadStatus();
    });

    return () => {
      clearInterval(interval);
      unsub();
    };
  }, [loadStatus]);

  const handleRefresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    setFeedback(null);
    try {
      const res = await api.refreshSources();
      setFeedback(res.message || 'RSS Feed refreshed successfully');
      await loadStatus();
      if (onRefreshCompleted) {
        onRefreshCompleted();
      }
      setTimeout(() => setFeedback(null), 4000);
    } catch (e: any) {
      setFeedback(`Refresh failed: ${e.message || 'Network error'}`);
    } finally {
      setRefreshing(false);
    }
  };

  const handleModeToggle = async (newMode: SystemMode) => {
    if (switchingMode || status?.current_mode === newMode) return;
    setSwitchingMode(true);
    try {
      await api.setMode(newMode);
      await loadStatus();
      if (onRefreshCompleted) {
        onRefreshCompleted();
      }
    } catch {
      // Error
    } finally {
      setSwitchingMode(false);
    }
  };

  const isLive = status?.current_mode === 'LIVE';
  const isConnected = status?.status === 'CONNECTED';
  const isFailed = status?.status === 'FAILED';

  return (
    <div className="card bg-surface-800/80 border border-white/[0.08] p-4 rounded-xl shadow-lg mb-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        {/* Left: Source Identity & Mode */}
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${
            isLive 
              ? (isConnected ? 'bg-risk-low/15 border-risk-low/40 text-risk-low' : 'bg-risk-critical/15 border-risk-critical/40 text-risk-critical') 
              : 'bg-accent-blue/15 border-accent-blue/40 text-accent-blue'
          }`}>
            {isLive ? <Globe className="w-5 h-5 animate-pulse-slow" /> : <Layers className="w-5 h-5" />}
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-white tracking-tight">
                {isLive ? 'Google News RSS Feed' : 'Demo Crisis Simulation'}
              </span>
              
              {/* Connection Status Badge */}
              {isLive ? (
                isConnected ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-risk-low/20 text-risk-low border border-risk-low/30">
                    <CheckCircle2 className="w-3 h-3" /> CONNECTED
                  </span>
                ) : isFailed ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-risk-critical/20 text-risk-critical border border-risk-critical/30 animate-pulse">
                    <AlertCircle className="w-3 h-3" /> LIVE SOURCE UNAVAILABLE
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-500/20 text-gray-300 border border-gray-500/30">
                    INITIALIZING...
                  </span>
                )
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent-blue/20 text-accent-blue border border-accent-blue/30">
                  <Sparkles className="w-3 h-3" /> DEMO MODE
                </span>
              )}
            </div>

            <p className="text-xs text-gray-400 mt-0.5">
              {isLive 
                ? `Auto-polling Google News RSS every ${status?.poll_interval_seconds || 45}s for top Indian financial brands`
                : 'Simulating synthetic crisis scenarios & social spikes for hackathon evaluation'}
            </p>
          </div>
        </div>

        {/* Right: Mode Selector & Refresh Action */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-end flex-wrap">
          {/* Mode Switcher Pill */}
          <div className="flex items-center bg-surface-900 border border-white/10 rounded-lg p-1">
            <button
              onClick={() => handleModeToggle('LIVE')}
              disabled={switchingMode}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                isLive
                  ? 'bg-gradient-to-r from-risk-low/80 to-emerald-600 text-white shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              🟢 LIVE RSS
            </button>
            <button
              onClick={() => handleModeToggle('DEMO')}
              disabled={switchingMode}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                !isLive
                  ? 'bg-accent-blue text-white shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              🔵 DEMO
            </button>
          </div>

          {/* Refresh Sources Button */}
          {isLive && (
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="btn-primary flex items-center gap-2 text-xs py-1.5 px-3 bg-white/10 hover:bg-white/15 text-white border border-white/15 shadow-none"
              title="Trigger immediate Google News RSS fetch"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-accent-blue' : ''}`} />
              <span>{refreshing ? 'Fetching...' : 'Refresh Sources'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      {isLive && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-white/[0.06] text-xs">
          <div>
            <span className="text-gray-500 block">Last Fetch:</span>
            <span className="text-gray-200 font-medium font-mono">
              {formatTimestamp(status?.last_successful_fetch || undefined)}
            </span>
          </div>
          <div>
            <span className="text-gray-500 block">Articles Ingested:</span>
            <span className="text-emerald-400 font-bold font-mono">
              {status?.articles_ingested_total ?? 0}
            </span>
          </div>
          <div>
            <span className="text-gray-500 block">Last Article Published:</span>
            <span className="text-gray-200 font-medium font-mono">
              {formatTimestamp(status?.last_article_published || undefined)}
            </span>
          </div>
          <div>
            <span className="text-gray-500 block">Monitored Queries:</span>
            <span className="text-gray-300 font-medium truncate block" title={status?.monitored_queries?.join(', ') || 'Active Brands'}>
              {status?.monitored_queries?.length ? `${status.monitored_queries.length} Monitored Queries` : 'Active Brands'}
            </span>
          </div>
        </div>
      )}

      {/* Error or Feedback Banner */}
      {isFailed && status?.last_error && isLive && (
        <div className="mt-3 p-2.5 rounded-lg bg-risk-critical/15 border border-risk-critical/30 text-risk-critical text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span><strong>LIVE SOURCE UNAVAILABLE:</strong> {status.last_error}. Retrying automatically on next cycle.</span>
        </div>
      )}

      {feedback && (
        <div className="mt-3 p-2 rounded-lg bg-accent-blue/15 border border-accent-blue/30 text-accent-cyan text-xs">
          {feedback}
        </div>
      )}
    </div>
  );
}
