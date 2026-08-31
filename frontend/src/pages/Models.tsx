import React, { useEffect, useState } from 'react';
import { Cpu, Plus, CheckCircle, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import { fetchApi } from '../lib/api';
import { ModelRecord, ProviderInfo } from '../types';

export const Models: React.FC = () => {
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Add Model Form State
  const [newModel, setNewModel] = useState({
    id: '',
    name: '',
    provider: 'ollama',
    type: 'LOCAL',
    tier: 'BALANCED',
    context_window: 32768,
    quality_score: 0.85,
    speed_score: 0.85,
    cost_per_input_token: 0.0,
    cost_per_output_token: 0.0,
    supports_coding: true,
    supports_reasoning: true,
    supports_vision: false,
    supports_tools: true,
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [m, p] = await Promise.all([
        fetchApi<ModelRecord[]>('/api/models'),
        fetchApi<ProviderInfo[]>('/api/providers'),
      ]);
      setModels(m);
      setProviders(p);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newModel.id || !newModel.name) return;
    try {
      await fetchApi('/api/models', {
        method: 'POST',
        body: JSON.stringify(newModel),
      });
      setShowAddModal(false);
      loadData();
    } catch (err: any) {
      alert(`Error creating model: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-text-primary tracking-wide flex items-center gap-2">
            <Cpu className="w-5 h-5 text-accent-primary" />
            MODEL REGISTRY & PROVIDER STATUS
          </h2>
          <p className="text-xs text-text-muted font-mono mt-1">
            Manage active candidate models, context windows, benchmark metadata, and provider adapters.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={loadData}
            className="p-2 rounded-lg border border-border-subtle bg-bg-card text-text-muted hover:text-text-primary"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-accent-primary text-bg-primary font-bold hover:brightness-110 shadow-[0_0_12px_rgba(77,163,255,0.3)] transition-all"
          >
            <Plus className="w-3.5 h-3.5" /> ADD MODEL
          </button>
        </div>
      </div>

      {/* 1. PROVIDER CONNECTIVITY STATUS CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
        {providers.map((p) => {
          const isConnected = p.status === 'CONNECTED' || p.status === 'READY';
          return (
            <div
              key={p.id}
              className="p-3.5 rounded-xl border border-border-subtle bg-bg-card space-y-2 font-mono text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-text-primary">{p.name}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    isConnected ? 'bg-accent-success animate-pulse' : 'bg-text-dim'
                  }`}
                />
              </div>
              <div className="text-[11px] text-text-muted">
                Status: <strong className={isConnected ? 'text-accent-success' : 'text-text-dim'}>{p.status}</strong>
              </div>
              <p className="text-[10px] text-text-dim truncate">
                {p.credentials_status}
              </p>
            </div>
          );
        })}
      </div>

      {/* Notice on security */}
      <div className="p-3 rounded-lg border border-border-subtle bg-bg-secondary/60 font-mono text-xs text-text-muted flex items-center justify-between">
        <span>🔒 External provider API keys are read securely from your local environment (<code className="text-text-primary">.env</code>) and are never exposed in browser responses.</span>
      </div>

      {/* 2. MODELS REGISTRY TABLE */}
      <div className="rounded-xl border border-border-subtle bg-bg-card p-5 space-y-4 overflow-x-auto">
        <h3 className="font-mono text-xs font-bold text-text-primary uppercase tracking-wider">
          Registered Candidate Models ({models.length})
        </h3>
        
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-border-subtle text-text-muted">
              <th className="pb-2.5">Model ID</th>
              <th className="pb-2.5">Provider</th>
              <th className="pb-2.5">Tier</th>
              <th className="pb-2.5">Context Window</th>
              <th className="pb-2.5">Capabilities</th>
              <th className="pb-2.5">Quality / Speed</th>
              <th className="pb-2.5">Pricing (1K In/Out)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle/40">
            {models.map((m) => (
              <tr key={m.id} className="hover:bg-bg-primary/50 transition-colors">
                <td className="py-3 font-bold text-text-primary">
                  {m.name}
                  <span className="block text-[11px] text-text-muted font-normal">{m.id}</span>
                </td>
                <td className="py-3">
                  <span className="px-2 py-0.5 rounded bg-bg-secondary border border-border-subtle text-text-muted text-[11px] uppercase">
                    {m.provider}
                  </span>
                </td>
                <td className="py-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                    m.tier === 'POWER' ? 'bg-purple-500/20 text-purple-400' : (m.tier === 'BALANCED' ? 'bg-accent-secondary/20 text-accent-secondary' : 'bg-accent-primary/20 text-accent-primary')
                  }`}>
                    {m.tier}
                  </span>
                </td>
                <td className="py-3 text-text-primary font-bold">
                  {m.context_window.toLocaleString()}
                </td>
                <td className="py-3">
                  <div className="flex flex-wrap gap-1 text-[10px]">
                    {m.supports_coding && <span className="px-1.5 py-0.2 rounded bg-accent-primary/10 text-accent-primary">Code</span>}
                    {m.supports_reasoning && <span className="px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-400">Reason</span>}
                    {m.supports_vision && <span className="px-1.5 py-0.2 rounded bg-accent-secondary/10 text-accent-secondary">Vision</span>}
                    {m.supports_tools && <span className="px-1.5 py-0.2 rounded bg-accent-success/10 text-accent-success">Tools</span>}
                  </div>
                </td>
                <td className="py-3 text-text-muted">
                  <strong className="text-text-primary">{(m.quality_score * 100).toFixed(0)}%</strong> Q / <strong className="text-text-primary">{(m.speed_score * 100).toFixed(0)}%</strong> S
                </td>
                <td className="py-3">
                  {m.cost_per_input_token === 0 ? (
                    <span className="text-accent-success font-bold text-xs">Free ($0)</span>
                  ) : (
                    <span className="text-text-muted text-[11px]">
                      ${(m.cost_per_input_token * 1000).toFixed(4)} / ${(m.cost_per_output_token * 1000).toFixed(4)}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Model Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-bg-card border border-border-subtle rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl font-mono">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
              Register New Model
            </h3>
            
            <form onSubmit={handleAddModel} className="space-y-3 text-xs">
              <div>
                <label className="text-text-muted block mb-1">Model Identifier (ID):</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ollama-custom-mistral"
                  value={newModel.id}
                  onChange={(e) => setNewModel({ ...newModel, id: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary focus:border-accent-primary outline-none"
                />
              </div>

              <div>
                <label className="text-text-muted block mb-1">Display Name:</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mistral 7B Instruct v0.3"
                  value={newModel.name}
                  onChange={(e) => setNewModel({ ...newModel, name: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary focus:border-accent-primary outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-text-muted block mb-1">Provider:</label>
                  <select
                    value={newModel.provider}
                    onChange={(e) => setNewModel({ ...newModel, provider: e.target.value })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  >
                    <option value="ollama">Ollama (Local)</option>
                    <option value="mock">Mock / Demo</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                </div>

                <div>
                  <label className="text-text-muted block mb-1">Tier:</label>
                  <select
                    value={newModel.tier}
                    onChange={(e) => setNewModel({ ...newModel, tier: e.target.value })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  >
                    <option value="FAST">FAST</option>
                    <option value="BALANCED">BALANCED</option>
                    <option value="POWER">POWER</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-text-muted block mb-1">Context Window:</label>
                  <input
                    type="number"
                    value={newModel.context_window}
                    onChange={(e) => setNewModel({ ...newModel, context_window: Number(e.target.value) })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  />
                </div>
                <div>
                  <label className="text-text-muted block mb-1">Quality Score (0-1):</label>
                  <input
                    type="number"
                    step="0.05"
                    value={newModel.quality_score}
                    onChange={(e) => setNewModel({ ...newModel, quality_score: Number(e.target.value) })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  />
                </div>
              </div>

              {/* Capabilities checkboxes */}
              <div className="pt-2 border-t border-border-subtle flex flex-wrap gap-4 text-[11px]">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newModel.supports_coding}
                    onChange={(e) => setNewModel({ ...newModel, supports_coding: e.target.checked })}
                  />
                  <span>Supports Coding</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newModel.supports_reasoning}
                    onChange={(e) => setNewModel({ ...newModel, supports_reasoning: e.target.checked })}
                  />
                  <span>Supports Reasoning</span>
                </label>
              </div>

              <div className="pt-4 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg border border-border-subtle bg-bg-secondary text-text-muted hover:text-text-primary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-accent-primary text-bg-primary font-bold hover:brightness-110"
                >
                  Save Model
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
