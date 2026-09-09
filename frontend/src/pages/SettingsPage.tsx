import React, { useEffect, useState } from 'react';
import { Sliders, Shield, DollarSign, Cpu, CheckCircle, Sun, Moon } from 'lucide-react';
import { fetchApi } from '../lib/api';
import { useTheme } from '../ThemeContext';

export const SettingsPage: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [budget, setBudget] = useState<{
    daily_limit: number;
    monthly_limit: number;
    per_request_limit: number;
    current_monthly_spend: number;
    intervention_mode: string;
  } | null>(null);

  useEffect(() => {
    fetchApi<any>('/api/budgets').then(setBudget).catch(console.error);
  }, []);

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-16 font-mono">
      <div className="border-b border-border-subtle pb-4 flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-text-primary tracking-wide flex items-center gap-2">
            <Sliders className="w-5 h-5 text-accent-primary" />
            SYSTEM CONFIGURATION & BUDGET GUARDS
          </h2>
          <p className="text-xs text-text-muted mt-1">
            Configure daily and monthly spend limits, routing threshold interventions, and environment parameters.
          </p>
        </div>
        
        <button 
          onClick={toggleTheme}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-secondary border border-border-subtle text-text-muted hover:text-text-primary hover:border-border-active transition-all text-xs font-bold"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          {theme === 'dark' ? 'LIGHT MODE' : 'DARK MODE'}
        </button>
      </div>

      {/* Budget Management */}
      <div className="rounded-xl border border-border-subtle bg-bg-card p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-accent-success" />
            Budget Thresholds & Automated Interventions
          </h3>
          <span className="text-[10px] px-2 py-0.5 rounded bg-accent-success/20 text-accent-success font-bold">
            Intervention Mode: {budget?.intervention_mode || 'NORMAL'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-bg-primary border border-border-subtle">
            <span className="text-text-muted block text-[11px]">Monthly Limit</span>
            <span className="text-lg font-bold text-text-primary mt-1 block">
              ${budget?.monthly_limit?.toFixed(2) || '100.00'}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-bg-primary border border-border-subtle">
            <span className="text-text-muted block text-[11px]">Current Monthly Spend</span>
            <span className="text-lg font-bold text-accent-primary mt-1 block">
              ${budget?.current_monthly_spend?.toFixed(4) || '0.0000'}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-bg-primary border border-border-subtle">
            <span className="text-text-muted block text-[11px]">Daily Limit</span>
            <span className="text-lg font-bold text-text-primary mt-1 block">
              ${budget?.daily_limit?.toFixed(2) || '10.00'}
            </span>
          </div>
        </div>

        {/* Budget Intervention Legend */}
        <div className="space-y-2 pt-2 text-[11px] text-text-muted">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-success" />
            <span>&lt; 80% Budget: Standard balanced multi-criteria routing</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-secondary" />
            <span>&gt;= 80% Budget: Cost optimization weighting enabled</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-error" />
            <span>&gt;= 95% Budget: Hard prefer local / zero-cost models</span>
          </div>
        </div>
      </div>

      {/* Security & Secrets */}
      <div className="rounded-xl border border-border-subtle bg-bg-card p-6 space-y-4">
        <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
          <Shield className="w-4 h-4 text-accent-primary" />
          Security Policy & Secrets Architecture
        </h3>
        <p className="text-xs text-text-muted leading-relaxed">
          Model Router operates under a zero-secret-exposure contract. API tokens are stored only in environment files (<code className="text-text-primary">.env</code>), never stored as plain text in browser databases, and automatically redacted from server logs.
        </p>
      </div>

    </div>
  );
};
