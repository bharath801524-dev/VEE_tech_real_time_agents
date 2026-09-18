import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Radio, AlertTriangle, BarChart2, Timer,
  Users, Bell, Settings, Menu, Zap, ChevronRight
} from 'lucide-react';
import { wsService } from './services/websocket';
import { cn } from './utils';

// Pages
import Dashboard from './pages/Dashboard';
import LiveFeed from './pages/LiveFeed';
import CrisisCenter from './pages/CrisisCenter';
import Analytics from './pages/Analytics';
import SLAMonitor from './pages/SLAMonitor';
import Clients from './pages/Clients';
import Alerts from './pages/Alerts';
import SettingsPage from './pages/Settings';

// Global crisis notification
import CrisisNotification from './components/CrisisNotification';
import type { WSMessage } from './types';

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/feed', icon: Radio, label: 'Live Feed' },
  { path: '/crises', icon: AlertTriangle, label: 'Crisis Center' },
  { path: '/analytics', icon: BarChart2, label: 'Analytics' },
  { path: '/sla', icon: Timer, label: 'SLA Monitor' },
  { path: '/clients', icon: Users, label: 'Clients' },
  { path: '/alerts', icon: Bell, label: 'Alerts' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const location = useLocation();
  return (
    <>
      {/* Mobile overlay */}
      {open && <div className="fixed inset-0 bg-black/60 z-30 lg:hidden" onClick={onClose} />}
      <aside className={cn(
        'fixed top-0 left-0 h-full w-60 bg-surface-800 border-r border-white/[0.07] z-40 flex flex-col transition-transform duration-300',
        open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        {/* Logo */}
        <div className="p-5 border-b border-white/[0.07]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-blue to-accent-violet flex items-center justify-center shadow-lg shadow-accent-blue/30">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">MindMesh</h1>
              <p className="text-[10px] text-gray-500 font-medium">AI Crisis Intelligence</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto scrollbar-thin">
          {NAV_ITEMS.map(({ path, icon: Icon, label }) => {
            const active = location.pathname === path || (path !== '/' && location.pathname.startsWith(path));
            return (
              <NavLink
                key={path}
                to={path}
                onClick={onClose}
                className={active ? 'sidebar-link-active' : 'sidebar-link'}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-sm">{label}</span>
                {active && <ChevronRight className="w-3 h-3 ml-auto opacity-60" />}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/[0.07]">
          <div className="text-xs text-gray-500 text-center">
            <span className="text-gradient font-semibold">From 6-Hour</span> to{' '}
            <span className="text-risk-critical font-semibold">2-Min</span> Response
          </div>
        </div>
      </aside>
    </>
  );
}

function AppInner() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [crisisAlert, setCrisisAlert] = useState<WSMessage | null>(null);
  const [sourceStatus, setSourceStatus] = useState<any>(null);

  const loadStatus = async () => {
    try {
      const s = await wsService.connected;
      setWsConnected(s);
      const res = await fetch('http://localhost:8000/api/ingestion/status').then(r => r.json());
      setSourceStatus(res);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    wsService.connect();
    loadStatus();
    const unsub = wsService.on('CONNECTED', () => { setWsConnected(true); loadStatus(); });
    const crisisUnsub = wsService.on('ALERT_TRIGGERED', (msg) => setCrisisAlert(msg));
    const modeUnsub = wsService.on('MODE_CHANGE', () => loadStatus());
    const timer = setInterval(() => {
      setWsConnected(wsService.connected);
      loadStatus();
    }, 5000);
    return () => { unsub(); crisisUnsub(); modeUnsub(); clearInterval(timer); };
  }, []);

  const isLive = sourceStatus?.current_mode === 'LIVE';

  return (
    <div className="min-h-screen flex">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 lg:ml-60 flex flex-col min-h-screen">
        {/* Top header bar */}
        <header className="sticky top-0 z-20 bg-surface-900/90 backdrop-blur border-b border-white/[0.06] px-4 py-2.5 flex items-center justify-between gap-3 flex-wrap">
          <button
            className="lg:hidden p-1.5 rounded-lg hover:bg-white/10 transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <div className="flex-1 hidden sm:block">
            <span className="text-xs text-gray-400 font-medium">
              Real-Time Brand Intelligence & 2-Minute Crisis Response Engine
            </span>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            {/* System Status */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.04] border border-white/[0.08] rounded-lg text-xs">
              <span className="text-gray-400">System:</span>
              <div className={cn('w-2 h-2 rounded-full', wsConnected ? 'bg-risk-low animate-pulse-slow' : 'bg-risk-critical')} />
              <span className={cn('font-semibold', wsConnected ? 'text-risk-low' : 'text-risk-critical')}>
                {wsConnected ? 'ONLINE' : 'CONNECTING'}
              </span>
            </div>

            {/* Data Source Indicator */}
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${
              isLive
                ? (sourceStatus?.status === 'CONNECTED' 
                    ? 'bg-risk-low/15 border-risk-low/40 text-risk-low' 
                    : 'bg-risk-critical/15 border-risk-critical/40 text-risk-critical animate-pulse')
                : 'bg-accent-blue/15 border-accent-blue/40 text-accent-blue'
            }`}>
              <span>Data Mode:</span>
              <span>{isLive ? 'LIVE' : 'DEMO'}</span>
              <span className="opacity-50">•</span>
              <span className="font-normal">{isLive ? 'Google News RSS' : 'Simulated'}</span>
            </div>
          </div>
        </header>

        {/* Crisis notification overlay */}
        {crisisAlert && (
          <CrisisNotification
            message={crisisAlert}
            onDismiss={() => setCrisisAlert(null)}
          />
        )}

        {/* Page content */}
        <main className="flex-1 p-4 md:p-6 max-w-[1600px] w-full mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/feed" element={<LiveFeed />} />
            <Route path="/crises" element={<CrisisCenter />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/sla" element={<SLAMonitor />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  );
}
