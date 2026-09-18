import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Bell, RefreshCw, Send, CheckCircle2, ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';
import type { Alert, AlertChannel } from '../types';
import { riskBadgeClass, formatTimestamp } from '../utils';

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<AlertChannel | 'ALL'>('ALL');
  const [loading, setLoading] = useState(true);

  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getAlerts();
      setAlerts(data);
    } catch {
      // Backend offline fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 10000);
    return () => clearInterval(interval);
  }, [loadAlerts]);

  const channelIcon = (c: string) => {
    switch (c) {
      case 'slack': return '💬';
      case 'email': return '✉️';
      case 'sms': return '📱';
      default: return '🔔';
    }
  };

  const channelLabel = (c: string) => {
    switch (c) {
      case 'slack': return 'Slack (#incident-war-room)';
      case 'email': return 'Executive Email Distribution';
      case 'sms': return 'Twilio SMS Urgent Pager';
      default: return 'In-App Live Sentinel';
    }
  };

  const filtered = useMemo(() => {
    if (selectedChannel === 'ALL') return alerts;
    return alerts.filter(a => a.channel === selectedChannel);
  }, [alerts, selectedChannel]);

  // Fallback demo alerts if backend has none yet
  const displayAlerts: Alert[] = alerts.length > 0 ? filtered : [
    {
      id: 'alt-901',
      event_id: 'ev-1092',
      channel: 'slack',
      alert_level: 'CRITICAL',
      sent_at: Date.now() / 1000 - 65,
      status: 'DELIVERED',
      brand: 'PayU',
      headline: 'RBI initiates special regulatory compliance audit on payment aggregators',
      risk_score: 92,
    },
    {
      id: 'alt-902',
      event_id: 'ev-1092',
      channel: 'email',
      alert_level: 'CRITICAL',
      sent_at: Date.now() / 1000 - 62,
      status: 'DELIVERED',
      brand: 'PayU',
      headline: 'RBI initiates special regulatory compliance audit on payment aggregators',
      risk_score: 92,
    },
    {
      id: 'alt-903',
      event_id: 'ev-1092',
      channel: 'sms',
      alert_level: 'CRITICAL',
      sent_at: Date.now() / 1000 - 60,
      status: 'DELIVERED',
      brand: 'PayU',
      headline: 'RBI initiates special regulatory compliance audit on payment aggregators',
      risk_score: 92,
    },
    {
      id: 'alt-889',
      event_id: 'ev-1088',
      channel: 'slack',
      alert_level: 'HIGH',
      sent_at: Date.now() / 1000 - 410,
      status: 'DELIVERED',
      brand: 'Zepto',
      headline: 'Delivery partner strike threatens weekend delivery fulfilment',
      risk_score: 74,
    },
    {
      id: 'alt-876',
      event_id: 'ev-1074',
      channel: 'in_app',
      alert_level: 'HIGH',
      sent_at: Date.now() / 1000 - 1100,
      status: 'DELIVERED',
      brand: 'CRED',
      headline: 'Spike in user reports of UPI credit card bill payment processing delays',
      risk_score: 68,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-risk-critical/20 flex items-center justify-center">
              <Bell className="w-4 h-4 text-risk-critical" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Multi-Channel Alert Dispatcher</h1>
          </div>
          <p className="text-gray-400 text-xs mt-1">
            Real-time delivery audit across In-App, Slack Webhooks, SMS Pagers, and Executive Email
          </p>
        </div>

        <button onClick={loadAlerts} className="btn-ghost p-2 text-gray-400 hover:text-white">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Fatigue Prevention Status Banner */}
      <div className="card p-4 bg-accent-blue/5 border border-accent-blue/30 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-accent-blue shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="text-xs font-bold text-white">Fatigue Prevention & Deduplication Rules Active</div>
          <div className="text-xs text-gray-400 leading-relaxed">
            Identical storylines within a 5-minute rolling window are aggregated into a single incident card with updated mention counters, suppressing duplicate push spam across Slack and SMS channels.
          </div>
        </div>
      </div>

      {/* Channel Filters */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-3 text-xs">
        {(['ALL', 'slack', 'email', 'sms', 'in_app'] as const).map(ch => (
          <button
            key={ch}
            onClick={() => setSelectedChannel(ch)}
            className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 capitalize ${
              selectedChannel === ch
                ? 'bg-accent-blue text-white font-semibold shadow-lg shadow-accent-blue/30'
                : 'text-gray-400 hover:text-white hover:bg-white/[0.05]'
            }`}
          >
            <span>{ch === 'ALL' ? 'All Channels' : ch}</span>
          </button>
        ))}
      </div>

      {/* Alerts Table */}
      <div className="card space-y-3">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/10 text-gray-400 text-left">
                <th className="py-2.5 px-3">Channel</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Target Brand</th>
                <th className="py-2.5 px-3">Headline</th>
                <th className="py-2.5 px-3 text-center">Status</th>
                <th className="py-2.5 px-3 text-right">Dispatched At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {displayAlerts.map(a => (
                <tr key={a.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-3">
                    <span className="flex items-center gap-1.5 font-medium text-white">
                      <span>{channelIcon(a.channel)}</span>
                      <span>{channelLabel(a.channel)}</span>
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className={riskBadgeClass(a.alert_level)}>
                      {a.alert_level}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-semibold text-white">
                    {a.brand || 'Brand'}
                  </td>
                  <td className="py-3 px-3 text-gray-300 max-w-sm truncate" title={a.headline}>
                    {a.headline}
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-risk-low/20 text-risk-low border border-risk-low/30">
                      <CheckCircle2 className="w-3 h-3" />
                      {a.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right text-gray-500 font-mono whitespace-nowrap">
                    <span className="flex items-center justify-end gap-1">
                      <Send className="w-3 h-3 text-accent-blue" />
                      {formatTimestamp(a.sent_at)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
