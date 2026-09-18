import { useState, useEffect, useCallback } from 'react';
import {
  Settings as SettingsIcon, Save, RefreshCw, Check, Sliders, BellRing, Cpu
} from 'lucide-react';
import { api } from '../services/api';
import type { Settings } from '../types';

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    mode: 'DEMO',
    risk_threshold: 60,
    critical_threshold: 80,
    cooldown_seconds: 300,
    alerts_in_app: true,
    alerts_slack: true,
    alerts_email: true,
    alerts_sms: true,
    sla_target_seconds: 120,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const loadSettings = useCallback(async () => {
    try {
      setLoading(true);
      const s = await api.getSettings();
      setSettings(s);
    } catch {
      // Backend offline fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleSave = async () => {
    try {
      setSaving(true);
      const updated = await api.updateSettings(settings);
      setSettings(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch {
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-surface-700 flex items-center justify-center">
              <SettingsIcon className="w-4 h-4 text-accent-blue" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">System & AI Configuration</h1>
          </div>
          <p className="text-gray-400 text-xs mt-1">
            Configure risk thresholds, SLA targets, alert channels, and fatigue suppression parameters
          </p>
        </div>

        <div className="flex items-center gap-2">
          {savedSuccess && (
            <span className="text-xs text-risk-low flex items-center gap-1 font-semibold animate-fade-in">
              <Check className="w-4 h-4" /> Settings Saved
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button onClick={loadSettings} className="btn-ghost p-2 text-gray-400 hover:text-white">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* System Mode Switch */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-accent-violet" />
          <h3 className="font-bold text-white text-sm">Operation Mode</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          <button
            type="button"
            onClick={() => setSettings(prev => ({ ...prev, mode: 'DEMO' }))}
            className={`p-4 rounded-xl border text-left transition-all ${
              settings.mode === 'DEMO'
                ? 'bg-accent-blue/10 border-accent-blue text-white shadow-lg shadow-accent-blue/10'
                : 'bg-surface-900 border-white/10 text-gray-400 hover:text-white'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-bold text-sm">Demo Simulation Mode</span>
              {settings.mode === 'DEMO' && <span className="w-2 h-2 rounded-full bg-accent-blue" />}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Deterministic, hyper-fast scenario injection with zero external API key requirements.
            </p>
          </button>

          <button
            type="button"
            onClick={() => setSettings(prev => ({ ...prev, mode: 'LIVE' }))}
            className={`p-4 rounded-xl border text-left transition-all ${
              settings.mode === 'LIVE'
                ? 'bg-risk-low/10 border-risk-low text-white shadow-lg shadow-risk-low/10'
                : 'bg-surface-900 border-white/10 text-gray-400 hover:text-white'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-bold text-sm">Live Production Pipeline</span>
              {settings.mode === 'LIVE' && <span className="w-2 h-2 rounded-full bg-risk-low" />}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Connects to live NewsAPI, Twitter, Reddit, Slack Webhook, and Gemini LLM.
            </p>
          </button>
        </div>
      </div>

      {/* Threshold Sliders */}
      <div className="card space-y-5">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-accent-blue" />
          <h3 className="font-bold text-white text-sm">Risk Thresholds & SLA Controls</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          {/* High Risk Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-gray-300 font-medium">High-Risk Alert Threshold</label>
              <span className="font-mono font-bold text-risk-high text-sm">{settings.risk_threshold} / 100</span>
            </div>
            <input
              type="range"
              min={30}
              max={90}
              value={settings.risk_threshold}
              onChange={e => setSettings(prev => ({ ...prev, risk_threshold: Number(e.target.value) }))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <p className="text-[11px] text-gray-500">Events scoring at or above this trigger High-Risk team routing.</p>
          </div>

          {/* Critical Risk Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-gray-300 font-medium">Critical Crisis Threshold</label>
              <span className="font-mono font-bold text-risk-critical text-sm">{settings.critical_threshold} / 100</span>
            </div>
            <input
              type="range"
              min={60}
              max={95}
              value={settings.critical_threshold}
              onChange={e => setSettings(prev => ({ ...prev, critical_threshold: Number(e.target.value) }))}
              className="w-full accent-rose-500 cursor-pointer"
            />
            <p className="text-[11px] text-gray-500">Events scoring at or above this trigger immediate C-Suite and SMS pagers.</p>
          </div>

          {/* SLA Target Seconds */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-gray-300 font-medium">SLA Target Response Time</label>
              <span className="font-mono font-bold text-accent-blue text-sm">{settings.sla_target_seconds} seconds</span>
            </div>
            <input
              type="range"
              min={60}
              max={300}
              step={10}
              value={settings.sla_target_seconds}
              onChange={e => setSettings(prev => ({ ...prev, sla_target_seconds: Number(e.target.value) }))}
              className="w-full accent-blue-500 cursor-pointer"
            />
            <p className="text-[11px] text-gray-500">Target latency budget from ingestion to multi-channel alert dispatch.</p>
          </div>

          {/* Fatigue Cooldown */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-gray-300 font-medium">Fatigue Suppression Cooldown</label>
              <span className="font-mono font-bold text-accent-violet text-sm">{settings.cooldown_seconds} seconds ({Math.round(settings.cooldown_seconds / 60)}m)</span>
            </div>
            <input
              type="range"
              min={60}
              max={900}
              step={30}
              value={settings.cooldown_seconds}
              onChange={e => setSettings(prev => ({ ...prev, cooldown_seconds: Number(e.target.value) }))}
              className="w-full accent-purple-500 cursor-pointer"
            />
            <p className="text-[11px] text-gray-500">Suppresses duplicate push alerts for identical ongoing incidents.</p>
          </div>
        </div>
      </div>

      {/* Multi-Channel Alerts */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <BellRing className="w-4 h-4 text-risk-low" />
          <h3 className="font-bold text-white text-sm">Dispatched Notification Channels</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {[
            { key: 'alerts_in_app' as const, label: 'In-App Live Sentinel & WebSocket Popups', icon: '🔔' },
            { key: 'alerts_slack' as const, label: 'Slack Webhook (#incident-war-room)', icon: '💬' },
            { key: 'alerts_email' as const, label: 'Executive Email Crisis Briefings', icon: '✉️' },
            { key: 'alerts_sms' as const, label: 'Twilio Urgent SMS Pager (C-Suite)', icon: '📱' },
          ].map(ch => (
            <label
              key={ch.key}
              className="flex items-center justify-between p-3 rounded-lg bg-surface-900 border border-white/[0.08] cursor-pointer hover:border-white/20 transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <span className="text-base">{ch.icon}</span>
                <span className="text-gray-200 font-medium">{ch.label}</span>
              </div>
              <input
                type="checkbox"
                checked={settings[ch.key]}
                onChange={e => setSettings(prev => ({ ...prev, [ch.key]: e.target.checked }))}
                className="w-4 h-4 rounded bg-surface-800 border-white/20 text-accent-blue focus:ring-0 cursor-pointer"
              />
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
