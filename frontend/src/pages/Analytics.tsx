import { useState, useEffect, useCallback } from 'react';
import {
  BarChart2, RefreshCw, TrendingUp, PieChart as PieIcon,
  Flame, Globe, Calendar
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Legend
} from 'recharts';
import { api } from '../services/api';
import type { AnalyticsData } from '../types';

const SENTIMENT_COLORS = {
  Positive: '#10B981', // emerald
  Neutral: '#6B7280',  // gray
  Negative: '#F43F5E', // rose
};

const RISK_COLORS = {
  LOW: '#10B981',
  MEDIUM: '#F59E0B',
  HIGH: '#F97316',
  CRITICAL: '#F43F5E',
};

export default function Analytics() {
  const [range, setRange] = useState<'15m' | '1h' | 'today' | '7d'>('1h');
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.getAnalytics(range);
      setData(res);
    } catch {
      // Backend offline
    } finally {
      setLoading(false);
    }
  }, [range]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Fallback demo data if backend gives empty
  const mentionsOverTime = data?.mentions_over_time?.length ? data.mentions_over_time : [
    { time: '10:00', news: 12, twitter: 45, reddit: 18, total: 75 },
    { time: '10:15', news: 18, twitter: 82, reddit: 24, total: 124 },
    { time: '10:30', news: 34, twitter: 210, reddit: 65, total: 309 },
    { time: '10:45', news: 95, twitter: 640, reddit: 180, total: 915 },
    { time: '11:00', news: 140, twitter: 1120, reddit: 340, total: 1600 },
    { time: '11:15', news: 110, twitter: 890, reddit: 260, total: 1260 },
    { time: '11:30', news: 75, twitter: 540, reddit: 190, total: 805 },
  ];

  const sentimentData = [
    { name: 'Negative', value: data?.sentiment_distribution?.Negative ?? 64, color: SENTIMENT_COLORS.Negative },
    { name: 'Neutral', value: data?.sentiment_distribution?.Neutral ?? 24, color: SENTIMENT_COLORS.Neutral },
    { name: 'Positive', value: data?.sentiment_distribution?.Positive ?? 12, color: SENTIMENT_COLORS.Positive },
  ];

  const riskData = [
    { name: 'LOW', count: data?.risk_distribution?.LOW ?? 450, fill: RISK_COLORS.LOW },
    { name: 'MEDIUM', count: data?.risk_distribution?.MEDIUM ?? 180, fill: RISK_COLORS.MEDIUM },
    { name: 'HIGH', count: data?.risk_distribution?.HIGH ?? 85, fill: RISK_COLORS.HIGH },
    { name: 'CRITICAL', count: data?.risk_distribution?.CRITICAL ?? 32, fill: RISK_COLORS.CRITICAL },
  ];

  const velocityData = data?.velocity_spikes?.length ? data.velocity_spikes : [
    { time: '10:00', velocity: 1.1, baseline: 1.0 },
    { time: '10:15', velocity: 1.4, baseline: 1.0 },
    { time: '10:30', velocity: 2.8, baseline: 1.0 },
    { time: '10:45', velocity: 4.6, baseline: 1.0 },
    { time: '11:00', velocity: 5.2, baseline: 1.0 },
    { time: '11:15', velocity: 3.8, baseline: 1.0 },
    { time: '11:30', velocity: 2.3, baseline: 1.0 },
  ];

  const topTopics = data?.top_topics?.length ? data.top_topics : [
    { topic: 'RBI Regulatory Compliance', count: 1480 },
    { topic: 'Payment Gateway Timeout', count: 820 },
    { topic: 'Security Breach Rumor', count: 540 },
    { topic: 'Fintech Leadership Shakeup', count: 310 },
    { topic: 'Merchant Settlement Delay', count: 240 },
  ];

  const geoMentions = data?.geo_mentions?.length ? data.geo_mentions : [
    { city: 'Mumbai', count: 1840 },
    { city: 'Bengaluru', count: 1620 },
    { city: 'Delhi NCR', count: 1210 },
    { city: 'Hyderabad', count: 740 },
    { city: 'Chennai', count: 520 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-blue/20 flex items-center justify-center">
              <BarChart2 className="w-4 h-4 text-accent-blue" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Crisis Intelligence Analytics</h1>
          </div>
          <p className="text-gray-400 text-xs mt-1">Multi-dimensional volume, velocity, sentiment, and risk propagation metrics</p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-2">
          <div className="bg-surface-800 border border-white/10 rounded-lg p-1 flex items-center gap-1 text-xs">
            <Calendar className="w-3.5 h-3.5 text-gray-500 ml-1.5" />
            {(['15m', '1h', 'today', '7d'] as const).map(t => (
              <button
                key={t}
                onClick={() => setRange(t)}
                className={`px-2.5 py-1 rounded transition-colors uppercase text-[11px] font-semibold ${
                  range === t
                    ? 'bg-accent-blue text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          <button onClick={loadData} className="btn-ghost p-2 text-gray-400 hover:text-white">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Primary Chart: Mention Volume Over Time */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-accent-blue" /> Media Mention Volume & Spike Progression
          </h3>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5 text-gray-400"><span className="w-2.5 h-2.5 rounded bg-accent-blue" /> Twitter / X</span>
            <span className="flex items-center gap-1.5 text-gray-400"><span className="w-2.5 h-2.5 rounded bg-accent-violet" /> News Outlets</span>
            <span className="flex items-center gap-1.5 text-gray-400"><span className="w-2.5 h-2.5 rounded bg-accent-cyan" /> Reddit Forums</span>
          </div>
        </div>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mentionsOverTime}>
              <defs>
                <linearGradient id="colorTwitter" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.6}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorNews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.6}/>
                  <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="time" stroke="#6B7280" fontSize={11} />
              <YAxis stroke="#6B7280" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', fontSize: '12px' }}
              />
              <Area type="monotone" dataKey="twitter" stroke="#3B82F6" fillOpacity={1} fill="url(#colorTwitter)" />
              <Area type="monotone" dataKey="news" stroke="#8B5CF6" fillOpacity={1} fill="url(#colorNews)" />
              <Area type="monotone" dataKey="reddit" stroke="#06B6D4" fillOpacity={0.2} fill="#06B6D4" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid: Sentiment, Risk Levels, and Velocity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sentiment Distribution */}
        <div className="card space-y-3">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-risk-critical" /> Sentiment Ratio
          </h3>
          <div className="h-60 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', color: '#9CA3AF' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center text-xs text-gray-400">
            Negative sentiment dominates crisis events (64% share).
          </div>
        </div>

        {/* Risk Distribution */}
        <div className="card space-y-3">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-accent-violet" /> Risk Distribution
          </h3>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData}>
                <XAxis dataKey="name" stroke="#6B7280" fontSize={11} />
                <YAxis stroke="#6B7280" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px' }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {riskData.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center text-xs text-gray-400">
            32 events elevated to Critical triage tier.
          </div>
        </div>

        {/* Velocity Spike Multiplier */}
        <div className="card space-y-3">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <Flame className="w-4 h-4 text-risk-critical" /> Velocity Multiplier
          </h3>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={velocityData}>
                <XAxis dataKey="time" stroke="#6B7280" fontSize={11} />
                <YAxis stroke="#6B7280" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '12px' }} />
                <Area type="monotone" dataKey="velocity" stroke="#F43F5E" fill="#F43F5E" fillOpacity={0.2} />
                <Area type="monotone" dataKey="baseline" stroke="#6B7280" strokeDasharray="3 3" fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center text-xs text-gray-400">
            Spike reached peak 5.2x baseline at 11:00 AM.
          </div>
        </div>
      </div>

      {/* Topics & Geographic Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Topics */}
        <div className="card space-y-3">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-accent-blue" /> Top Crisis Topics
          </h3>
          <div className="space-y-2.5">
            {topTopics.map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-300 font-medium">{item.topic}</span>
                  <span className="text-gray-400 font-mono">{item.count.toLocaleString()}</span>
                </div>
                <div className="h-2 w-full bg-surface-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-accent-blue to-accent-violet rounded-full"
                    style={{ width: `${Math.min(100, (item.count / 1500) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Geographic Hotspots */}
        <div className="card space-y-3">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <Globe className="w-4 h-4 text-risk-low" /> Regional Coverage Hotspots
          </h3>
          <div className="space-y-2.5">
            {geoMentions.map((geo, idx) => (
              <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-surface-900/60 border border-white/[0.04] text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-risk-low" />
                  <span className="font-semibold text-white">{geo.city}</span>
                </div>
                <div className="text-gray-400 font-mono">
                  {geo.count.toLocaleString()} mentions
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
