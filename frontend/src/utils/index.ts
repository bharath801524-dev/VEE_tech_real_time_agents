import type { RiskLevel, Sentiment } from '../types';

export function riskColor(level?: RiskLevel | string): string {
  switch (level) {
    case 'CRITICAL': return 'text-risk-critical';
    case 'HIGH': return 'text-risk-high';
    case 'MEDIUM': return 'text-risk-medium';
    case 'LOW': return 'text-risk-low';
    default: return 'text-gray-400';
  }
}

export function riskBg(level?: RiskLevel | string): string {
  switch (level) {
    case 'CRITICAL': return 'bg-risk-critical';
    case 'HIGH': return 'bg-risk-high';
    case 'MEDIUM': return 'bg-risk-medium';
    case 'LOW': return 'bg-risk-low';
    default: return 'bg-gray-500';
  }
}

export function riskBadgeClass(level?: RiskLevel | string): string {
  switch (level) {
    case 'CRITICAL': return 'badge-critical';
    case 'HIGH': return 'badge-high';
    case 'MEDIUM': return 'badge-medium';
    case 'LOW': return 'badge-low';
    default: return 'badge-low';
  }
}

export function sentimentColor(s?: Sentiment | string): string {
  switch (s) {
    case 'Positive': return 'text-risk-low';
    case 'Negative': return 'text-risk-critical';
    default: return 'text-gray-400';
  }
}

export function sentimentIcon(s?: Sentiment | string): string {
  switch (s) {
    case 'Positive': return '↑';
    case 'Negative': return '↓';
    default: return '→';
  }
}

export function sourceIcon(s?: string): string {
  switch (s) {
    case 'news': return '📰';
    case 'twitter': return '𝕏';
    case 'reddit': return '🤖';
    default: return '📡';
  }
}

export function sourceLabel(s?: string): string {
  switch (s) {
    case 'news': return 'News';
    case 'twitter': return 'X/Twitter';
    case 'reddit': return 'Reddit';
    default: return 'Unknown';
  }
}

export function formatTimestamp(ts?: number): string {
  if (!ts) return '—';
  return new Date(ts * 1000).toLocaleTimeString('en-IN', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function formatSeconds(s?: number): string {
  if (s === undefined || s === null) return '—';
  if (s < 60) return `${Math.round(s)}s`;
  const m = Math.floor(s / 60);
  const sec = Math.round(s % 60);
  return `${m}m ${sec}s`;
}

export function formatNumber(n?: number): string {
  if (n === undefined || n === null) return '0';
  return n.toLocaleString('en-IN');
}

export function velocityClass(ratio?: number): string {
  if (!ratio) return 'text-gray-400';
  if (ratio >= 4) return 'text-risk-critical font-bold';
  if (ratio >= 2.5) return 'text-risk-high font-semibold';
  if (ratio >= 1.5) return 'text-risk-medium';
  return 'text-risk-low';
}

export function slaStatusBadge(passed?: boolean): string {
  return passed ? 'bg-risk-low/20 text-risk-low border border-risk-low/40 rounded-full px-2 py-0.5 text-xs font-semibold'
                : 'bg-risk-critical/20 text-risk-critical border border-risk-critical/40 rounded-full px-2 py-0.5 text-xs font-semibold';
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
