import React, { useState, useEffect } from 'react';
import { 
  Trophy, 
  Play, 
  RefreshCw, 
  TrendingDown, 
  TrendingUp, 
  Clock, 
  DollarSign, 
  ShieldCheck, 
  Sparkles,
  Award,
  CheckCircle2,
  XCircle,
  BarChart2
} from 'lucide-react';
import { fetchApi } from '../lib/api';
import { BenchmarkReport, BenchmarkCandidate, ModelRecord } from '../types';

export const BenchmarksPage: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>('gsm8k');
  const [sampleLimit, setSampleLimit] = useState<number>(5);
  const [baselineModel, setBaselineModel] = useState<string>('gpt-4o');
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [report, setReport] = useState<BenchmarkReport | null>(null);

  useEffect(() => {
    // Load dataset list and models
    fetchApi<{ datasets: any[] }>('/api/benchmarks/datasets')
      .then((res) => setDatasets(res.datasets))
      .catch(console.error);

    fetchApi<ModelRecord[]>('/api/models')
      .then(setModels)
      .catch(console.error);
  }, []);

  const runBenchmark = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<BenchmarkReport>('/api/benchmarks/run', {
        method: 'POST',
        body: JSON.stringify({
          dataset: selectedDataset,
          limit: sampleLimit,
          baseline_model: baselineModel,
        }),
      });
      setReport(data);
    } catch (err: any) {
      alert(`Benchmark execution failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16 font-sans">
      
      {/* 1. Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-text-primary tracking-wide flex items-center gap-2">
            <Trophy className="w-5 h-5 text-accent-primary" />
            AUTOMATED BENCHMARK SUITE & PARETO EVALUATOR
          </h2>
          <p className="text-xs text-text-muted font-mono mt-1">
            Empirical accuracy retention vs cost savings benchmark across GSM8K, HumanEval, and MMLU datasets.
          </p>
        </div>

        <button
          onClick={runBenchmark}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-accent-primary text-bg-primary font-mono text-xs font-bold hover:brightness-110 shadow-[0_0_15px_rgba(56,148,255,0.3)] transition-all disabled:opacity-50 cursor-pointer shrink-0"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" /> RUNNING BENCHMARK...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" /> RUN BENCHMARK EVALUATION
            </>
          )}
        </button>
      </div>

      {/* 2. Benchmark Configuration Bar */}
      <div className="rounded-2xl glass-panel p-5 border border-border-subtle grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
        
        {/* Dataset Selection */}
        <div className="space-y-1.5">
          <label className="text-text-muted font-bold block text-[11px]">BENCHMARK DATASET</label>
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            className="w-full rounded-xl border border-border-subtle bg-bg-card px-3 py-2.5 text-text-primary outline-none focus:border-accent-primary transition-all"
          >
            <option value="gsm8k">GSM8K (Math Multi-Step Reasoning)</option>
            <option value="humaneval">HumanEval (Python Code Synthesis & Tests)</option>
            <option value="mmlu">MMLU (General Multi-Domain Knowledge)</option>
          </select>
        </div>

        {/* Sample Limit */}
        <div className="space-y-1.5">
          <label className="text-text-muted font-bold block text-[11px]">SAMPLE COUNT ({sampleLimit} questions)</label>
          <input
            type="range"
            min="2"
            max="10"
            value={sampleLimit}
            onChange={(e) => setSampleLimit(parseInt(e.target.value))}
            className="w-full accent-accent-primary cursor-pointer mt-3"
          />
        </div>

        {/* Baseline Model */}
        <div className="space-y-1.5">
          <label className="text-text-muted font-bold block text-[11px]">BASELINE FRONTIER MODEL</label>
          <select
            value={baselineModel}
            onChange={(e) => setBaselineModel(e.target.value)}
            className="w-full rounded-xl border border-border-subtle bg-bg-card px-3 py-2.5 text-text-primary outline-none focus:border-accent-primary transition-all"
          >
            <option value="gpt-4o">gpt-4o (OpenAI)</option>
            <option value="claude-3-5-sonnet">claude-3-5-sonnet (Anthropic)</option>
            <option value="gemini-1.5-pro">gemini-1.5-pro (Google)</option>
            <option value="deepseek-chat">deepseek-chat (DeepSeek)</option>
          </select>
        </div>
      </div>

      {/* 3. Benchmark Results & Pareto Frontier */}
      {report ? (
        <div className="space-y-6">
          
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl glass-panel border border-border-subtle space-y-1">
              <span className="font-mono text-[10px] text-text-muted uppercase font-bold">DATASET EVALUATED</span>
              <div className="text-lg font-bold font-mono text-accent-primary">{report.dataset_name}</div>
              <span className="text-[11px] font-mono text-text-dim">{report.sample_count} samples</span>
            </div>

            <div className="p-4 rounded-2xl glass-panel border border-border-subtle space-y-1">
              <span className="font-mono text-[10px] text-text-muted uppercase font-bold">PARETO OPTIMAL POLICIES</span>
              <div className="text-lg font-bold font-mono text-accent-success">{report.pareto_frontier.length} Configurations</div>
              <span className="text-[11px] font-mono text-text-dim">Non-dominated frontier</span>
            </div>

            <div className="p-4 rounded-2xl glass-panel border border-border-subtle space-y-1">
              <span className="font-mono text-[10px] text-text-muted uppercase font-bold">BASELINE MODEL</span>
              <div className="text-lg font-bold font-mono text-text-primary">{report.baseline_model}</div>
              <span className="text-[11px] font-mono text-text-dim">Reference anchor</span>
            </div>

            <div className="p-4 rounded-2xl glass-panel border border-border-subtle space-y-1">
              <span className="font-mono text-[10px] text-text-muted uppercase font-bold">EVALUATION TIME</span>
              <div className="text-lg font-bold font-mono text-purple-400">{report.generated_at.slice(11, 19)} UTC</div>
              <span className="text-[11px] font-mono text-text-dim">Deterministic verification</span>
            </div>
          </div>

          {/* Pareto Frontier Performance Table */}
          <div className="rounded-2xl glass-panel border border-border-subtle p-5 space-y-4 overflow-x-auto">
            <div className="flex items-center justify-between">
              <h3 className="font-mono text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
                <Award className="w-4 h-4 text-accent-primary" />
                Pareto Frontier & Multi-Criteria Evaluation Matrix
              </h3>
              <span className="font-mono text-[11px] text-text-muted">
                [*] = Non-dominated Pareto frontier
              </span>
            </div>

            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-border-subtle text-text-muted text-[11px]">
                  <th className="pb-3">Candidate / Policy</th>
                  <th className="pb-3">Accuracy</th>
                  <th className="pb-3">Retention vs Baseline</th>
                  <th className="pb-3">Latency (Avg / p95)</th>
                  <th className="pb-3">Cost / 1K Reqs</th>
                  <th className="pb-3">Cost Savings</th>
                  <th className="pb-3 text-right">Pareto Optimal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/40">
                {report.candidates.map((c) => (
                  <tr key={c.name} className="hover:bg-bg-primary/50 transition-colors">
                    <td className="py-3 font-bold text-text-primary">
                      <span className={`px-2 py-0.5 rounded text-[11px] ${c.target_type === 'policy' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30' : 'bg-bg-secondary text-text-muted'}`}>
                        {c.name}
                      </span>
                    </td>
                    <td className="py-3 font-semibold text-text-primary">
                      {c.accuracy_percent.toFixed(1)}% ({c.correct_samples}/{c.total_samples})
                    </td>
                    <td className="py-3 font-semibold text-text-secondary">
                      {c.accuracy_retention_percent.toFixed(1)}%
                    </td>
                    <td className="py-3 text-text-muted">
                      {c.avg_latency_ms.toFixed(0)}ms / {c.p95_latency_ms.toFixed(0)}ms
                    </td>
                    <td className="py-3 text-text-primary font-bold">
                      ${c.avg_cost_per_1k_usd.toFixed(4)}
                    </td>
                    <td className="py-3 font-bold">
                      <span className={c.cost_savings_percent >= 0 ? 'text-accent-success' : 'text-accent-error'}>
                        {c.cost_savings_percent >= 0 ? '+' : ''}{c.cost_savings_percent.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      {c.is_pareto_optimal ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-accent-success/15 border border-accent-success/40 text-accent-success font-bold text-[10px]">
                          <CheckCircle2 className="w-3 h-3" /> YES (Frontier)
                        </span>
                      ) : (
                        <span className="text-text-dim text-[11px]">
                          Dominated
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ASCII Pareto Scatter Graph */}
          {report.ascii_graph && (
            <div className="rounded-2xl glass-panel border border-border-subtle p-5 space-y-3">
              <h4 className="font-mono text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-accent-secondary" />
                Cost vs Accuracy Pareto Frontier Curve
              </h4>
              <div className="p-4 rounded-xl bg-black/80 border border-border-subtle font-mono text-[11px] text-green-400 overflow-x-auto whitespace-pre leading-snug">
                {report.ascii_graph}
              </div>
            </div>
          )}

        </div>
      ) : (
        <div className="rounded-2xl glass-panel border border-border-subtle p-12 text-center space-y-4 max-w-xl mx-auto">
          <div className="w-12 h-12 rounded-2xl bg-accent-primary/10 border border-accent-primary/30 flex items-center justify-center mx-auto text-accent-primary">
            <Trophy className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold font-mono text-text-primary">No Benchmark Run Yet</h3>
          <p className="text-xs text-text-muted font-mono leading-relaxed">
            Click "Run Benchmark Evaluation" above to evaluate candidate model accuracy retention and cost savings across standardized test subsets.
          </p>
        </div>
      )}

    </div>
  );
};
