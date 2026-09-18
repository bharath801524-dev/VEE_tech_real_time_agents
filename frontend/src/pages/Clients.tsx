import { useState, useEffect, useCallback } from 'react';
import {
  Users, Plus, Trash2, Shield, RefreshCw, X, Check, Tag
} from 'lucide-react';
import { api } from '../services/api';
import type { Client } from '../types';

export default function Clients() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [tier, setTier] = useState('Tier-1');
  const [keywords, setKeywords] = useState('');
  const [competitors, setCompetitors] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadClients = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getClients();
      setClients(data);
    } catch {
      // Backend offline fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      setSaving(true);
      setError(null);
      const newClient = await api.createClient({
        name: name.trim(),
        tier,
        keywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
        competitors: competitors.split(',').map(c => c.trim()).filter(Boolean),
        is_active: true,
      });
      setClients(prev => [...prev, newClient]);
      setShowAddModal(false);
      setName('');
      setKeywords('');
      setCompetitors('');
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to stop monitoring this brand?')) return;
    try {
      await api.deleteClient(id);
      setClients(prev => prev.filter(c => c.id !== id));
    } catch {
      alert('Failed to delete client');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-violet/20 flex items-center justify-center">
              <Users className="w-4 h-4 text-accent-violet" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Monitored Client Portfolio</h1>
          </div>
          <p className="text-gray-400 text-xs mt-1">
            Configure enterprise brands, monitoring tiers, entity keywords, and competitor baskets
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary text-xs px-3.5 py-2 flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add Monitored Brand
          </button>
          <button onClick={loadClients} className="btn-ghost p-2 text-gray-400 hover:text-white">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Client List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading && clients.length === 0 ? (
          <div className="card col-span-full text-center py-12 text-gray-400 text-xs">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-accent-blue" />
            Loading monitored client portfolio...
          </div>
        ) : clients.length === 0 ? (
          <div className="card col-span-full text-center py-12 text-gray-500 text-xs">
            No monitored clients configured. Click "Add Monitored Brand" to get started.
          </div>
        ) : (
          clients.map(c => (
            <div key={c.id} className="card p-5 space-y-4 hover:border-white/20 transition-all">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">{c.name}</h3>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${
                      c.tier === 'Tier-1' ? 'bg-risk-critical/20 text-risk-critical border border-risk-critical/30' : 'bg-white/10 text-gray-300'
                    }`}>
                      {c.tier}
                    </span>
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5 flex items-center gap-1">
                    <Shield className="w-3 h-3 text-risk-low" /> 24/7 Priority Sentinel
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(c.id)}
                  className="text-gray-500 hover:text-risk-critical transition-colors p-1"
                  title="Remove client"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Keywords */}
              <div className="space-y-1.5">
                <div className="text-[11px] text-gray-400 font-medium flex items-center gap-1">
                  <Tag className="w-3 h-3 text-accent-blue" /> Ingestion Keywords ({c.keywords?.length || 0})
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {c.keywords?.map((k, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-surface-900 border border-white/[0.08] text-[10px] text-gray-300">
                      {k}
                    </span>
                  ))}
                </div>
              </div>

              {/* Competitors */}
              {c.competitors && c.competitors.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-white/[0.06]">
                  <div className="text-[11px] text-gray-500 font-medium">Competitor Basket</div>
                  <div className="flex flex-wrap gap-1.5">
                    {c.competitors.map((comp, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-accent-violet/10 text-accent-violet text-[10px]">
                        {comp}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Add Client Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-800 border border-white/15 rounded-xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="font-bold text-white text-base">Add Monitored Brand</h3>
              <button onClick={() => setShowAddModal(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {error && (
              <div className="p-2.5 bg-risk-critical/10 border border-risk-critical/30 rounded text-xs text-risk-critical">
                {error}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-gray-300 font-medium">Brand / Client Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Swiggy, Paytm, Zomato"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="w-full bg-surface-900 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-blue"
                />
              </div>

              <div className="space-y-1">
                <label className="text-gray-300 font-medium">Priority Tier</label>
                <select
                  value={tier}
                  onChange={e => setTier(e.target.value)}
                  className="w-full bg-surface-900 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none"
                >
                  <option value="Tier-1">Tier-1 (Executive Escalation, 0 Cooldown)</option>
                  <option value="Tier-2">Tier-2 (Standard Risk Monitoring)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-gray-300 font-medium">Keywords (comma separated)</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Swiggy, Instamart, delivery, food tech"
                  value={keywords}
                  onChange={e => setKeywords(e.target.value)}
                  className="w-full bg-surface-900 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-blue"
                />
              </div>

              <div className="space-y-1">
                <label className="text-gray-300 font-medium">Competitors (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g. Zomato, Zepto, Blinkit"
                  value={competitors}
                  onChange={e => setCompetitors(e.target.value)}
                  className="w-full bg-surface-900 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-blue"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-ghost px-4 py-2"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-primary px-4 py-2 flex items-center gap-1.5"
                >
                  <Check className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Add Brand'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
