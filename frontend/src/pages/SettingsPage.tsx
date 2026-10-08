import React, { useEffect, useState } from 'react';
import { 
  Sliders, 
  Shield, 
  DollarSign, 
  Cpu, 
  CheckCircle, 
  Sun, 
  Moon,
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  Building2,
  Activity,
  Lock
} from 'lucide-react';
import { fetchApi } from '../lib/api';
import { useTheme } from '../ThemeContext';
import { Workspace, ApiKeyItem } from '../types';

export const SettingsPage: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [budget, setBudget] = useState<{
    daily_limit: number;
    monthly_limit: number;
    per_request_limit: number;
    current_monthly_spend: number;
    intervention_mode: string;
  } | null>(null);

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('default');
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKeyData, setCreatedKeyData] = useState<{ key: string; name: string } | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      const [b, ws, keys] = await Promise.all([
        fetchApi<any>('/api/budgets').catch(() => null),
        fetchApi<Workspace[]>('/api/auth/workspaces').catch(() => []),
        fetchApi<ApiKeyItem[]>('/api/auth/workspaces/default/keys').catch(() => []),
      ]);
      setBudget(b);
      setWorkspaces(ws);
      setApiKeys(keys);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setLoading(true);
    try {
      const res = await fetchApi<any>(`/api/auth/workspaces/${selectedWorkspace}/keys`, {
        method: 'POST',
        body: JSON.stringify({ name: newKeyName, rate_limit_rpm: 60 }),
      });
      setCreatedKeyData({ key: res.key, name: res.name });
      setNewKeyName('');
      loadData();
    } catch (err: any) {
      alert(`Failed to create API key: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key?')) return;
    try {
      await fetchApi(`/api/keys/${keyId}`, { method: 'DELETE' });
      loadData();
    } catch (err: any) {
      alert(`Failed to revoke key: ${err.message}`);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16 font-mono">
      
      {/* Header */}
      <div className="border-b border-border-subtle pb-4 flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-text-primary tracking-wide flex items-center gap-2">
            <Sliders className="w-5 h-5 text-accent-primary" />
            SYSTEM CONFIGURATION & ACCESS CONTROL
          </h2>
          <p className="text-xs text-text-muted mt-1">
            Manage multi-tenant workspaces, cryptographically hashed API keys, rate limits, and budget guards.
          </p>
        </div>
        
        <button 
          onClick={toggleTheme}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-bg-secondary border border-border-subtle text-text-muted hover:text-text-primary hover:border-border-active transition-all text-xs font-bold cursor-pointer"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-yellow-400" /> : <Moon className="w-4 h-4 text-purple-400" />}
          {theme === 'dark' ? 'LIGHT THEME' : 'DARK THEME'}
        </button>
      </div>

      {/* 1. API Keys & Workspace Management */}
      <div className="rounded-2xl glass-panel p-6 space-y-5 border border-border-subtle shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-3">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-accent-primary" />
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              API Keys & Multi-Tenant Workspaces
            </h3>
          </div>
          <button
            onClick={() => {
              setCreatedKeyData(null);
              setShowKeyModal(true);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-primary text-bg-primary font-bold text-xs hover:brightness-110 shadow-[0_0_12px_rgba(56,148,255,0.3)] transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" /> CREATE API KEY
          </button>
        </div>

        <div className="space-y-3">
          <p className="text-xs text-text-muted leading-relaxed">
            API keys allow external applications and SDKs (<code>modelrouter-sdk</code>) to authenticate using <code>Authorization: Bearer mr_live_...</code>.
          </p>

          <div className="overflow-x-auto rounded-xl border border-border-subtle bg-bg-primary/80">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border-subtle text-text-muted text-[11px]">
                  <th className="p-3">Key Name</th>
                  <th className="p-3">Key Prefix</th>
                  <th className="p-3">Workspace</th>
                  <th className="p-3">Rate Limit</th>
                  <th className="p-3">Created</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/40">
                {apiKeys.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-text-muted">
                      No API keys generated yet. Click "Create API Key" to generate a secure client token.
                    </td>
                  </tr>
                ) : (
                  apiKeys.map((k) => (
                    <tr key={k.id} className="hover:bg-bg-card/40 transition-colors">
                      <td className="p-3 font-bold text-text-primary">{k.name}</td>
                      <td className="p-3 text-accent-primary font-mono">{k.key_prefix}...</td>
                      <td className="p-3 text-text-muted">{k.workspace_id}</td>
                      <td className="p-3 text-text-muted">{k.rate_limit_rpm} RPM</td>
                      <td className="p-3 text-text-dim text-[11px]">{k.created_at ? k.created_at.slice(0, 10) : 'N/A'}</td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => handleRevokeKey(k.id)}
                          className="p-1.5 rounded-md hover:bg-red-500/20 text-red-400 transition-all cursor-pointer"
                          title="Revoke Key"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 2. Budget Thresholds & Automated Interventions */}
      <div className="rounded-2xl glass-panel p-6 space-y-4 border border-border-subtle shadow-lg">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-accent-success" />
            Budget Thresholds & Automated Interventions
          </h3>
          <span className="text-[10px] px-2 py-0.5 rounded bg-accent-success/20 text-accent-success font-bold">
            Mode: {budget?.intervention_mode || 'NORMAL'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-bg-primary/90 border border-border-subtle">
            <span className="text-text-muted block text-[11px]">Monthly Spend Limit</span>
            <span className="text-xl font-extrabold text-text-primary mt-1 block">
              ${budget?.monthly_limit ? budget.monthly_limit.toFixed(2) : '100.00'}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-bg-primary/90 border border-border-subtle">
            <span className="text-text-muted block text-[11px]">Current Period Spend</span>
            <span className="text-xl font-extrabold text-accent-primary mt-1 block">
              ${budget?.current_monthly_spend !== undefined ? budget.current_monthly_spend.toFixed(5) : '0.00000'}
            </span>
          </div>

          <div className="p-4 rounded-xl bg-bg-primary/90 border border-border-subtle">
            <span className="text-text-muted block text-[11px]">Daily Safety Cap</span>
            <span className="text-xl font-extrabold text-text-primary mt-1 block">
              ${budget?.daily_limit ? budget.daily_limit.toFixed(2) : '10.00'}
            </span>
          </div>
        </div>

        {/* Budget Intervention Rules */}
        <div className="space-y-2 pt-2 text-[11px] text-text-muted">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-success" />
            <span>&lt; 80% Budget: Standard multi-criteria weighted scoring</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-secondary" />
            <span>&gt;= 80% Budget: Automated cost-optimized policy weighting intervention</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-error" />
            <span>&gt;= 95% Budget: Hard constraint preferring local / zero-cost fallback models</span>
          </div>
        </div>
      </div>

      {/* 3. Security Policy & Observability Export */}
      <div className="rounded-2xl glass-panel p-6 space-y-4 border border-border-subtle shadow-lg">
        <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <Shield className="w-4 h-4 text-accent-primary" />
          Observability & Zero-Secret Security Architecture
        </h3>
        <p className="text-xs text-text-muted leading-relaxed">
          Model Router implements zero-secret logging. All upstream API tokens and private headers are redacted prior to persisting into the database or broadcasting over Redis SSE feeds.
        </p>
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <a
            href="http://localhost:8000/metrics"
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-2 rounded-lg bg-bg-primary border border-border-subtle text-xs text-accent-primary hover:border-accent-primary font-bold flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5" /> Prometheus Metrics (/metrics)
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-2 rounded-lg bg-bg-primary border border-border-subtle text-xs text-text-primary hover:border-accent-primary font-bold"
          >
            Interactive OpenAPI Docs (/docs)
          </a>
        </div>
      </div>

      {/* Modal: Create API Key */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="rounded-2xl glass-panel border border-border-subtle bg-bg-card p-6 max-w-md w-full space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border-subtle pb-3">
              <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
                <Key className="w-4 h-4 text-accent-primary" />
                {createdKeyData ? 'API Key Generated' : 'Create New API Key'}
              </h3>
              <button
                onClick={() => setShowKeyModal(false)}
                className="text-text-muted hover:text-text-primary text-xs"
              >
                ✕
              </button>
            </div>

            {createdKeyData ? (
              <div className="space-y-4">
                <div className="p-3.5 rounded-xl bg-accent-success/10 border border-accent-success/30 text-accent-success text-xs font-semibold">
                  API Key created successfully! Copy this key now. It will not be shown again.
                </div>
                
                <div className="space-y-1.5">
                  <label className="text-[11px] text-text-muted font-bold">API TOKEN</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value={createdKeyData.key}
                      className="w-full rounded-lg bg-black/80 border border-border-subtle px-3 py-2 text-xs font-mono text-green-400 outline-none select-all"
                    />
                    <button
                      onClick={() => copyToClipboard(createdKeyData.key)}
                      className="px-3 py-2 rounded-lg bg-accent-primary text-bg-primary font-bold text-xs flex items-center gap-1 cursor-pointer"
                    >
                      {copiedKey ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => setShowKeyModal(false)}
                  className="w-full py-2.5 rounded-xl bg-bg-secondary border border-border-subtle text-text-primary text-xs font-bold hover:bg-bg-primary cursor-pointer"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreateKey} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[11px] text-text-muted font-bold">KEY NAME / SERVICE IDENTIFIER</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. production-backend, mobile-client"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="w-full rounded-xl bg-bg-primary border border-border-subtle px-3.5 py-2.5 text-xs text-text-primary outline-none focus:border-accent-primary"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowKeyModal(false)}
                    className="px-4 py-2 rounded-xl bg-bg-secondary text-text-muted text-xs font-bold hover:text-text-primary cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-5 py-2 rounded-xl bg-accent-primary text-bg-primary text-xs font-bold hover:brightness-110 cursor-pointer disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Generate Key'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
};
