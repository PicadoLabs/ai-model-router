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
  Layers,
  Sparkles
} from 'lucide-react';
import { fetchApi } from '../lib/api';
import { SystemAnalytics, ModelRecord } from '../types';

const COLORS = ['#4DA3FF', '#38BDF8', '#A78BFA', '#4ADE80', '#F472B6', '#FBBF24', '#34D399'];

export const Analytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [models, setModels] = useState<ModelRecord[]>([]);
  
  // Cost Calculator State
  const [simMonthlyReqs, setSimMonthlyReqs] = useState<number>(25000);
  const [simAvgTokens, setSimAvgTokens] = useState<number>(800);
  const [selectedBaseline, setSelectedBaseline] = useState<string>('gpt-4o');

  useEffect(() => {
    fetchApi<SystemAnalytics>('/api/analytics').then(setAnalytics).catch(console.error);
    fetchApi<ModelRecord[]>('/api/models').then(setModels).catch(console.error);
  }, []);

  // Compute Cost Calculator Figures using actual model catalog rates
  const baselineModel = models.find((m) => m.id === selectedBaseline) || models[0];
  const baseInRate = baselineModel?.cost_per_input_token ?? 0.000005;
  const baseOutRate = baselineModel?.cost_per_output_token ?? 0.000015;
  const blendedBaseCostPerReq = (simAvgTokens * 0.35 * baseInRate) + (simAvgTokens * 0.65 * baseOutRate);
  
  // Average blended cost across active fast and local models in registry
  const fastModels = models.filter((m) => m.tier === 'FAST' || m.type === 'LOCAL');
  const avgFastInRate = fastModels.length > 0 ? (fastModels.reduce((acc, m) => acc + m.cost_per_input_token, 0) / fastModels.length) : 0;
  const avgFastOutRate = fastModels.length > 0 ? (fastModels.reduce((acc, m) => acc + m.cost_per_output_token, 0) / fastModels.length) : 0;
  const blendedFastCostPerReq = (simAvgTokens * 0.35 * avgFastInRate) + (simAvgTokens * 0.65 * avgFastOutRate);

  // Modeled routing mixture: 60% fast/local, 25% balanced, 15% frontier
  const simulatedAllBaselineCost = simMonthlyReqs * blendedBaseCostPerReq;
  const simulatedSmartRoutedCost = simMonthlyReqs * ((0.60 * blendedFastCostPerReq) + (0.25 * blendedBaseCostPerReq * 0.3) + (0.15 * blendedBaseCostPerReq));
  const simulatedSavings = Math.max(0, simulatedAllBaselineCost - simulatedSmartRoutedCost);
  const simulatedSavingsPct = simulatedAllBaselineCost > 0 ? (simulatedSavings / simulatedAllBaselineCost) * 100 : 0;

  // Prepare verified chart data from database
  const modelChartData = analytics?.model_distribution
    ? Object.entries(analytics.model_distribution).map(([name, count]) => ({ name, count }))
    : [];

  const taskChartData = analytics?.task_distribution
    ? Object.entries(analytics.task_distribution).map(([name, count]) => ({ name, count }))
    : [];

  const totalReqs = analytics?.total_requests || 0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16 font-mono">
      
      {/* Header */}
      <div className="border-b border-border-subtle pb-4">
        <h2 className="text-xl font-bold text-text-primary tracking-wide flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-accent-primary" />
          ROUTING ANALYTICS & COST EFFICIENCY
        </h2>
        <p className="text-xs text-text-muted mt-1">
          Historical request distributions, verified cost savings against baseline, and predictive volume modeling.
        </p>
      </div>

      {/* 1. COST SAVINGS COMPARISON CARD */}
      <div className="rounded-2xl glass-panel border border-accent-success/30 p-6 relative overflow-hidden shadow-xl">
        <div className="absolute right-0 top-0 w-64 h-64 bg-accent-success/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <span className="text-xs uppercase tracking-wider text-accent-success font-bold flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4" /> Verified Cost Savings vs Baseline
            </span>
            <div className="text-3xl md:text-4xl font-extrabold text-text-primary mt-1">
              ${(analytics?.savings?.cost_saved_usd || 0).toFixed(6)} USD
            </div>
            <p className="text-xs text-text-muted mt-1">
              Based on {totalReqs.toLocaleString()} routed requests compared against '{analytics?.savings?.baseline_model || 'Frontier Baseline'}'
            </p>
          </div>

          <div className="flex items-center gap-6 text-xs border-t md:border-t-0 md:border-l border-border-subtle pt-4 md:pt-0 md:pl-6">
            <div>
              <span className="text-text-muted block text-[10px]">All Baseline Cost</span>
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
        
        {/* Destination Model Distribution */}
        <div className="rounded-2xl glass-panel border border-border-subtle p-5 space-y-4">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
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
                    contentStyle={{ backgroundColor: '#101419', borderColor: '#242B33', borderRadius: '12px', fontSize: '12px', fontFamily: 'monospace' }} 
                  />
                  <Bar dataKey="count" fill="#38BDF8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-text-muted">
                No request telemetry logged yet.
              </div>
            )}
          </div>
        </div>

        {/* Task Classification Breakdown */}
        <div className="rounded-2xl glass-panel border border-border-subtle p-5 space-y-4">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-purple-400" />
            Task Classification Breakdown
          </h3>
          <div className="h-64 w-full">
            {taskChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={taskChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="count"
                  >
                    {taskChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#101419', borderColor: '#242B33', borderRadius: '12px', fontSize: '12px', fontFamily: 'monospace' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-text-muted">
                No task distributions recorded yet.
              </div>
            )}
          </div>
        </div>

      </div>

      {/* 3. INTERACTIVE ANNUAL COST SAVINGS SIMULATOR */}
      <div className="rounded-2xl glass-panel border border-border-subtle p-6 space-y-6">
        <div className="border-b border-border-subtle pb-3">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <Calculator className="w-4 h-4 text-accent-primary" />
            Enterprise Volume Cost Savings Simulator
          </h3>
          <p className="text-[11px] text-text-muted mt-1">
            Simulate monthly cost reductions based on your application's expected request throughput and token volume.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
          <div className="space-y-1.5">
            <label className="text-text-muted font-bold block text-[11px]">MONTHLY REQUEST VOLUME</label>
            <input 
              type="number"
              min="1000"
              step="5000"
              value={simMonthlyReqs}
              onChange={(e) => setSimMonthlyReqs(Math.max(1, parseInt(e.target.value) || 0))}
              className="w-full rounded-xl bg-bg-primary border border-border-subtle px-3.5 py-2.5 text-text-primary outline-none focus:border-accent-primary"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-text-muted font-bold block text-[11px]">AVERAGE TOKENS PER REQUEST</label>
            <input 
              type="number"
              min="100"
              step="100"
              value={simAvgTokens}
              onChange={(e) => setSimAvgTokens(Math.max(1, parseInt(e.target.value) || 0))}
              className="w-full rounded-xl bg-bg-primary border border-border-subtle px-3.5 py-2.5 text-text-primary outline-none focus:border-accent-primary"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-text-muted font-bold block text-[11px]">BASELINE FRONTIER MODEL</label>
            <select
              value={selectedBaseline}
              onChange={(e) => setSelectedBaseline(e.target.value)}
              className="w-full rounded-xl bg-bg-primary border border-border-subtle px-3.5 py-2.5 text-text-primary outline-none focus:border-accent-primary"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>{m.name} ({m.provider})</option>
              ))}
            </select>
          </div>
        </div>

        {/* Projected Figures */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-bg-primary/90 border border-border-subtle">
            <span className="text-[11px] text-text-muted block">Without Routing (All-Frontier)</span>
            <span className="text-xl font-extrabold text-text-primary mt-1 block">
              ${simulatedAllBaselineCost.toFixed(2)} / mo
            </span>
          </div>

          <div className="p-4 rounded-xl bg-bg-primary/90 border border-border-subtle">
            <span className="text-[11px] text-text-muted block">With Model Router Mixture</span>
            <span className="text-xl font-extrabold text-accent-primary mt-1 block">
              ${simulatedSmartRoutedCost.toFixed(2)} / mo
            </span>
          </div>

          <div className="p-4 rounded-xl bg-bg-primary/90 border border-accent-success/40">
            <span className="text-[11px] text-accent-success block font-bold">Projected Net Savings</span>
            <span className="text-xl font-extrabold text-accent-success mt-1 block">
              ${simulatedSavings.toFixed(2)} / mo ({simulatedSavingsPct.toFixed(1)}%)
            </span>
          </div>
        </div>
      </div>

    </div>
  );
};
