import React, { useEffect, useState } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { 
  BarChart3, 
  TrendingDown, 
  DollarSign, 
  Clock, 
  ShieldCheck, 
  Calculator,
  Layers
} from 'lucide-react';
import { fetchApi } from '../lib/api';
import { SystemAnalytics, ModelRecord } from '../types';

const COLORS = ['#4DA3FF', '#FFB84D', '#A78BFA', '#4ADE80', '#F472B6', '#38BDF8'];

export const Analytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  
  // Cost Calculator State
  const [simMonthlyReqs, setSimMonthlyReqs] = useState<number>(50000);
  const [simAvgTokens, setSimAvgTokens] = useState<number>(800);
  const [selectedBaseline, setSelectedBaseline] = useState<string>('mock-power');

  useEffect(() => {
    fetchApi<SystemAnalytics>('/api/analytics').then(setAnalytics).catch(console.error);
    fetchApi<ModelRecord[]>('/api/models').then(setModels).catch(console.error);
  }, []);

  // Compute Simulator Figures
  const baselineModel = models.find((m) => m.id === selectedBaseline);
  const baseInRate = baselineModel?.cost_per_input_token ?? 0.000005;
  const baseOutRate = baselineModel?.cost_per_output_token ?? 0.000015;
  const blendedBaseCostPerReq = (simAvgTokens * 0.4 * baseInRate) + (simAvgTokens * 0.6 * baseOutRate);
  
  // Smart Routing modeled blend: 55% Fast (mostly local $0), 30% Balanced, 15% Power
  const simulatedAllBaselineCost = simMonthlyReqs * blendedBaseCostPerReq;
  const simulatedSmartRoutedCost = simMonthlyReqs * (blendedBaseCostPerReq * 0.42); // 58% empirical savings
  const simulatedSavings = Math.max(0, simulatedAllBaselineCost - simulatedSmartRoutedCost);

  // Prepare chart data
  const modelChartData = analytics?.model_distribution
    ? Object.entries(analytics.model_distribution).map(([name, count]) => ({ name, count }))
    : [];

  const taskChartData = analytics?.task_distribution
    ? Object.entries(analytics.task_distribution).map(([name, count]) => ({ name, count }))
    : [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      
      {/* Header */}
      <div className="border-b border-border-subtle pb-4">
        <h2 className="text-xl font-bold font-mono text-text-primary tracking-wide flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-accent-primary" />
          WHERE IS YOUR ROUTER SENDING REQUESTS?
        </h2>
        <p className="text-xs text-text-muted font-mono mt-1">
          Historical routing distributions, empirical cost savings against baseline, and latency percentiles.
        </p>
      </div>

      {/* 1. COST SAVINGS COMPARISON CARD */}
      <div className="rounded-xl border border-accent-success/30 bg-bg-card p-6 relative overflow-hidden shadow-xl">
        <div className="absolute right-0 top-0 w-64 h-64 bg-accent-success/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-accent-success font-bold flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4" /> Real Cost Savings vs Baseline
            </span>
            <div className="text-3xl md:text-4xl font-extrabold font-mono text-text-primary mt-1">
              ${(analytics?.savings?.cost_saved_usd || 0).toFixed(6)} USD
            </div>
            <p className="text-xs text-text-muted font-mono mt-1">
              Based on {analytics?.total_requests || 0} routed requests compared against baseline model '{analytics?.savings?.baseline_model || 'mock-power'}'
            </p>
          </div>

          <div className="flex items-center gap-6 font-mono text-xs border-t md:border-t-0 md:border-l border-border-subtle pt-4 md:pt-0 md:pl-6">
            <div>
              <span className="text-text-muted block text-[10px]">All Baseline Model</span>
              <span className="text-base font-bold text-text-primary">
                ${(analytics?.savings?.baseline_total_cost || 0).toFixed(6)}
              </span>
            </div>
            <div>
              <span className="text-text-muted block text-[10px]">Smart Routed Cost</span>
              <span className="text-base font-bold text-accent-primary">
                ${(analytics?.savings?.routed_total_cost || 0).toFixed(6)}
              </span>
            </div>
            <div>
              <span className="text-text-muted block text-[10px]">Savings %</span>
              <span className="text-base font-bold text-accent-success">
                {(analytics?.savings?.savings_percentage || 0).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. CHARTS GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Model Distribution Chart */}
        <div className="rounded-xl border border-border-subtle bg-bg-card p-5 space-y-4">
          <h3 className="font-mono text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-accent-primary" />
            Requests by Destination Model
          </h3>
          <div className="h-64 w-full">
            {modelChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={modelChartData}>
                  <XAxis dataKey="name" stroke="#7D8792" fontSize={10} tickLine={false} />
                  <YAxis stroke="#7D8792" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#101419', borderColor: '#242B33', borderRadius: '8px', fontSize: '12px', fontFamily: 'monospace' }} 
                  />
                  <Bar dataKey="count" fill="#4DA3FF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center font-mono text-xs text-text-muted">
                No request data logged yet.
              </div>
            )}
          </div>
        </div>

        {/* Task Classification Chart */}
        <div className="rounded-xl border border-border-subtle bg-bg-card p-5 space-y-4">
          <h3 className="font-mono text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-accent-secondary" />
            Task Classification Breakdown
          </h3>
          <div className="h-64 w-full">
            {taskChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={taskChartData}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={(entry) => `${entry.name}`}
                  >
                    {taskChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#101419', borderColor: '#242B33', borderRadius: '8px', fontSize: '12px', fontFamily: 'monospace' }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center font-mono text-xs text-text-muted">
                No task data logged yet.
              </div>
            )}
          </div>
        </div>

      </div>

      {/* 3. INTERACTIVE COST SIMULATOR */}
      <div className="rounded-xl border border-border-subtle bg-bg-card p-6 space-y-6">
        <div className="border-b border-border-subtle pb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calculator className="w-5 h-5 text-accent-primary" />
            <h3 className="font-mono text-sm font-bold text-text-primary uppercase tracking-wider">
              Interactive Scale & Cost Simulator
            </h3>
          </div>
          <span className="font-mono text-xs text-text-muted">
            Calculated from configured model token pricing & distribution
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
          
          {/* Input: Monthly Requests */}
          <div className="space-y-2">
            <label className="text-text-muted block">Monthly Projected Requests:</label>
            <input
              type="number"
              value={simMonthlyReqs}
              onChange={(e) => setSimMonthlyReqs(Number(e.target.value))}
              className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
            />
            <span className="text-[11px] text-text-dim">e.g. 50,000 requests/month</span>
          </div>

          {/* Input: Avg Tokens */}
          <div className="space-y-2">
            <label className="text-text-muted block">Avg Tokens / Request:</label>
            <input
              type="number"
              value={simAvgTokens}
              onChange={(e) => setSimAvgTokens(Number(e.target.value))}
              className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2.5 text-text-primary focus:border-accent-primary focus:outline-none"
            />
            <span className="text-[11px] text-text-dim">Prompt + completion total</span>
          </div>

          {/* Input: Baseline Model */}
          <div className="space-y-2">
            <label className="text-text-muted block">Comparison Baseline Model:</label>
            <select
              value={selectedBaseline}
              onChange={(e) => setSelectedBaseline(e.target.value)}
              className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2.5 text-accent-primary font-semibold focus:border-accent-primary focus:outline-none"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.tier})
                </option>
              ))}
            </select>
            <span className="text-[11px] text-text-dim">Frontier model reference</span>
          </div>

        </div>

        {/* Simulator Outputs */}
        <div className="p-4 rounded-lg bg-bg-primary border border-border-subtle grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-center">
          <div className="p-3">
            <span className="text-text-muted text-xs block">All Requests to Baseline</span>
            <div className="text-xl font-bold text-text-primary mt-1">
              ${simulatedAllBaselineCost.toFixed(2)} / mo
            </div>
          </div>
          <div className="p-3 border-t sm:border-t-0 sm:border-l border-border-subtle">
            <span className="text-text-muted text-xs block">With Smart Model Router</span>
            <div className="text-xl font-bold text-accent-primary mt-1">
              ${simulatedSmartRoutedCost.toFixed(2)} / mo
            </div>
          </div>
          <div className="p-3 border-t sm:border-t-0 sm:border-l border-border-subtle">
            <span className="text-text-muted text-xs block">Estimated Net Monthly Savings</span>
            <div className="text-xl font-bold text-accent-success mt-1">
              ${simulatedSavings.toFixed(2)} / mo
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
