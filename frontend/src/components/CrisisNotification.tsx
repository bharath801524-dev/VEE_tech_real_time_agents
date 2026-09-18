import { useEffect } from 'react';
import { X, AlertTriangle, Clock } from 'lucide-react';
import type { WSMessage } from '../types';
import { formatTimestamp, riskBadgeClass } from '../utils';

interface Props {
  message: WSMessage;
  onDismiss: () => void;
}

export default function CrisisNotification({ message, onDismiss }: Props) {
  const data = message.data as Record<string, unknown>;

  useEffect(() => {
    const t = setTimeout(onDismiss, 15000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div className="fixed top-16 right-4 z-50 w-80 animate-slide-in">
      <div className="bg-surface-700 border border-risk-critical/50 rounded-xl shadow-2xl glow-critical overflow-hidden">
        {/* Header */}
        <div className="bg-risk-critical/20 px-4 py-2.5 flex items-center gap-2 border-b border-risk-critical/30">
          <div className="status-dot-red" />
          <span className="text-risk-critical font-bold text-sm uppercase tracking-wider">Critical Crisis Detected</span>
          <button onClick={onDismiss} className="ml-auto text-gray-400 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-risk-critical mt-0.5 shrink-0" />
            <div>
              <div className="font-bold text-white text-sm">{data.brand as string}</div>
              <div className="text-gray-300 text-xs mt-0.5 leading-relaxed">
                {(data.headline as string)?.substring(0, 80)}...
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className={riskBadgeClass(data.risk_level as string)}>
              {data.risk_level as string}
            </span>
            <span className="text-gray-400 text-xs font-mono">Score: {data.risk_score as number}/100</span>
          </div>

          {Boolean(data.what_happened) && (
            <p className="text-xs text-gray-400 leading-relaxed border-t border-white/10 pt-2">
              {(data.what_happened as string).substring(0, 100)}...
            </p>
          )}

          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>Detected {formatTimestamp(data.sent_at as number)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
