import React, { useState } from 'react';
import { 
  Send, 
  Cpu, 
  Zap, 
  Layers, 
  Clock, 
  DollarSign, 
  CheckCircle2, 
  XCircle, 
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  Sliders,
  Compass,
  ArrowRight,
  ShieldCheck,
  Code2,
  Bug,
  BookOpen,
  Terminal,
  Copy,
  Check,
  Activity
} from 'lucide-react';
import { fetchApi } from '../lib/api';
import { RequestAnalysis, RoutingDecision, ProviderResponse } from '../types';

export const Playground: React.FC = () => {
  const [prompt, setPrompt] = useState('Debug this distributed async task scheduler deadlock and suggest a thread-safe fix');
  const [policy, setPolicy] = useState('balanced');
  const [analyzerMode, setAnalyzerMode] = useState('rules');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'decision' | 'response' | 'candidates'>('decision');
  const [copied, setCopied] = useState(false);
  
  const [result, setResult] = useState<{
    request_id: string;
    analysis: RequestAnalysis;
    decision: RoutingDecision;
    response?: ProviderResponse;
    metrics?: any;
  } | null>(null);

  const [feedbackSent, setFeedbackSent] = useState(false);

  const handleRouteAndExecute = async (executeInference = true) => {
    if (!prompt.trim()) return;
    setLoading(true);
    setFeedbackSent(false);

    try {
      if (executeInference) {
        const data = await fetchApi<any>('/api/generate', {
          method: 'POST',
          body: JSON.stringify({ prompt, policy, analyzer_mode: analyzerMode }),
        });
        setResult(data);
      } else {
        const data = await fetchApi<any>('/api/route', {
          method: 'POST',
          body: JSON.stringify({ prompt, policy, analyzer_mode: analyzerMode }),
        });
        setResult(data);
      }
    } catch (err: any) {
      alert(`Routing execution failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (rating: number) => {
    if (!result?.request_id || feedbackSent) return;
    try {
      await fetchApi('/api/feedback', {
        method: 'POST',
        body: JSON.stringify({ request_id: result.request_id, rating }),
      });
      setFeedbackSent(true);
    } catch (err) {
      console.error(err);
    }
  };

  const copyResponse = () => {
    if (result?.response?.content) {
      navigator.clipboard.writeText(result.response.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border-subtle pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-primary/10 border border-accent-primary/30 flex items-center justify-center text-accent-primary shadow-[0_0_12px_rgba(56,148,255,0.2)]">
              <Compass className="w-4 h-4 text-accent-primary" />
            </div>
            <h2 className="text-xl font-bold font-mono text-text-primary tracking-wide">
              ROUTER PLAYGROUND & DECISION INSPECTION
            </h2>
          </div>
          <p className="text-xs text-text-muted font-mono mt-1 pl-10">
            Simulate real-time intent extraction, multi-criteria candidate scoring, and explainable model dispatch.
          </p>
        </div>

        {/* Global Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 glass-panel rounded-xl px-3 py-1.5 text-xs font-mono">
            <Sliders className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-text-muted">Routing Policy:</span>
            <select
              value={policy}
              onChange={(e) => setPolicy(e.target.value)}
              className="bg-transparent text-accent-primary font-bold outline-none cursor-pointer"
            >
              <option value="balanced" className="bg-bg-card text-text-primary">Balanced (Q35/C25/S20)</option>
              <option value="lowest_cost" className="bg-bg-card text-text-primary">Lowest Cost (C60)</option>
              <option value="lowest_latency" className="bg-bg-card text-text-primary">Lowest Latency (S60)</option>
              <option value="highest_quality" className="bg-bg-card text-text-primary">Highest Quality (Q65)</option>
              <option value="custom" className="bg-bg-card text-text-primary">Custom Weights</option>
            </select>
          </div>

          <div className="flex items-center gap-2 glass-panel rounded-xl px-3 py-1.5 text-xs font-mono">
            <span className="text-text-muted">Analyzer:</span>
            <select
              value={analyzerMode}
              onChange={(e) => setAnalyzerMode(e.target.value)}
              className="bg-transparent text-text-primary font-bold outline-none cursor-pointer"
            >
              <option value="rules" className="bg-bg-card text-text-primary">Deterministic Rules</option>
              <option value="llm" className="bg-bg-card text-text-primary">Optional LLM Classifier</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Request Input Panel */}
      <div className="rounded-2xl glass-panel p-6 space-y-4 shadow-xl border border-border-subtle grid-bg">
        <div className="flex items-center justify-between">
          <label className="text-xs font-mono uppercase tracking-wider text-text-muted font-bold flex items-center gap-2">
            <Terminal className="w-4 h-4 text-accent-primary" /> Prompt Ingress Buffer
          </label>
          <span className="text-[11px] font-mono text-text-dim">
            {prompt.length} chars • ~{Math.max(1, Math.floor(prompt.length / 4))} est. tokens
          </span>
        </div>

        <textarea
          rows={3}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter prompt to evaluate model routing..."
          className="w-full rounded-xl border border-border-subtle bg-bg-primary/90 p-4 font-mono text-sm text-text-primary placeholder:text-text-dim focus:border-accent-primary focus:ring-1 focus:ring-accent-primary/40 focus:outline-none transition-all shadow-inner"
        />

        <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
          {/* Quick preset chips */}
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <span className="text-text-dim text-[11px]">Test Presets:</span>
            <button
              onClick={() => setPrompt('Write a Python function to reverse a string and handle unicode edge cases')}
              className="px-2.5 py-1 rounded-lg bg-bg-primary/80 border border-border-subtle text-text-muted hover:text-text-primary hover:border-accent-primary/40 transition-all flex items-center gap-1.5 text-[11px]"
            >
              <Code2 className="w-3 h-3 text-accent-primary" /> Fast Code
            </button>
            <button
              onClick={() => setPrompt('Debug this distributed async deadlock in high-throughput worker pool and explain root cause')}
              className="px-2.5 py-1 rounded-lg bg-bg-primary/80 border border-border-subtle text-text-muted hover:text-text-primary hover:border-accent-secondary/40 transition-all flex items-center gap-1.5 text-[11px]"
            >
              <Bug className="w-3 h-3 text-accent-secondary" /> Deep Debug
            </button>
            <button
              onClick={() => setPrompt('Summarize this quarterly financial revenue breakdown into 3 bullet points')}
              className="px-2.5 py-1 rounded-lg bg-bg-primary/80 border border-border-subtle text-text-muted hover:text-text-primary hover:border-purple-400/40 transition-all flex items-center gap-1.5 text-[11px]"
            >
              <BookOpen className="w-3 h-3 text-purple-400" /> Summary
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3 font-mono">
            <button
              disabled={loading}
              onClick={() => handleRouteAndExecute(false)}
              className="px-4 py-2.5 rounded-xl border border-border-subtle bg-bg-primary/80 text-text-primary text-xs font-bold hover:border-accent-primary/60 transition-all disabled:opacity-50"
            >
              Dry Run (Analyze Only)
            </button>
            <button
              disabled={loading}
              onClick={() => handleRouteAndExecute(true)}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-accent-primary text-bg-primary text-xs font-extrabold hover:brightness-110 shadow-[0_0_20px_rgba(56,148,255,0.4)] transition-all disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              {loading ? 'Routing & Executing...' : 'ROUTE & EXECUTE →'}
            </button>
          </div>
        </div>
      </div>

      {/* Results & Inspection Section */}
      {result && (
        <div className="space-y-6 pt-2">
          
          {/* Inspection View Tabs */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-3 font-mono">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('decision')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'decision'
                    ? 'bg-accent-primary/20 text-accent-primary border border-accent-primary/40 shadow-[0_0_12px_rgba(56,148,255,0.15)]'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                1. Routing Decision & Explanation
              </button>
              {result.response && (
                <button
                  onClick={() => setActiveTab('response')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    activeTab === 'response'
                      ? 'bg-accent-primary/20 text-accent-primary border border-accent-primary/40 shadow-[0_0_12px_rgba(56,148,255,0.15)]'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  2. Response Stream ({result.metrics?.total_latency_ms || 0}ms)
                </button>
              )}
              <button
                onClick={() => setActiveTab('candidates')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'candidates'
                    ? 'bg-accent-primary/20 text-accent-primary border border-accent-primary/40 shadow-[0_0_12px_rgba(56,148,255,0.15)]'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                3. Candidate Scoreboard ({result.decision.candidate_scores.length})
              </button>
            </div>

            {/* Selected capsule */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-text-muted">Routed Destination:</span>
              <span className="px-2.5 py-1 rounded-lg bg-accent-primary/20 border border-accent-primary/40 text-accent-primary font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-accent-success" />
                {result.decision.selected_model_name}
              </span>
            </div>
          </div>

          {/* TAB 1: Decision & Request Analysis */}
          {activeTab === 'decision' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Structured Request Profile (Left 5 cols) */}
              <div className="lg:col-span-5 rounded-2xl glass-panel p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3 font-mono">
                  <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
                    <Activity className="w-4 h-4 text-accent-primary" /> Extracted Request Profile
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-bg-primary border border-border-subtle text-text-muted">
                    Mode: {result.analysis.analyzer_used}
                  </span>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  <div className="flex justify-between items-center py-1.5 border-b border-border-subtle/40">
                    <span className="text-text-muted">Task Classification</span>
                    <span className="font-bold text-accent-primary">{result.analysis.task_type}</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-border-subtle/40">
                    <span className="text-text-muted">Complexity Score</span>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-text-primary">{(result.analysis.complexity * 100).toFixed(0)}%</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        result.analysis.complexity_label === 'HIGH' ? 'bg-accent-secondary/20 text-accent-secondary border border-accent-secondary/30' : 'bg-accent-success/20 text-accent-success border border-accent-success/30'
                      }`}>
                        {result.analysis.complexity_label}
                      </span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-border-subtle/40">
                    <span className="text-text-muted">Multi-Step Reasoning</span>
                    <span className={result.analysis.reasoning_required ? 'text-accent-secondary font-bold' : 'text-text-dim'}>
                      {result.analysis.reasoning_required ? 'REQUIRED (True)' : 'Not Required'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-border-subtle/40">
                    <span className="text-text-muted">Syntactic / Code Logic</span>
                    <span className={result.analysis.coding_required ? 'text-accent-primary font-bold' : 'text-text-dim'}>
                      {result.analysis.coding_required ? 'REQUIRED (True)' : 'Not Required'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-border-subtle/40">
                    <span className="text-text-muted">Estimated Context</span>
                    <span className="text-text-primary font-bold">{result.analysis.context_size} tokens</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-border-subtle/40">
                    <span className="text-text-muted">Latency Priority</span>
                    <span className="text-text-primary">{result.analysis.latency_priority}</span>
                  </div>

                  <div className="flex justify-between items-center py-1.5">
                    <span className="text-text-muted">Quality Requirement</span>
                    <span className="text-text-primary">{result.analysis.quality_requirement}</span>
                  </div>
                </div>
              </div>

              {/* Explainable Decision Report (Right 7 cols) */}
              <div className="lg:col-span-7 rounded-2xl glass-panel p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3 font-mono">
                  <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-accent-success" />
                    Why This Model? (Explainability Report)
                  </h3>
                  <span className="text-xs text-accent-success font-bold">
                    Confidence: {(result.decision.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Selected Model Highlight Card */}
                <div className="p-4 rounded-xl bg-bg-primary/90 border border-accent-primary/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono shadow-md">
                  <div>
                    <span className="text-[10px] text-text-muted uppercase font-bold">Selected Destination</span>
                    <h4 className="text-base font-extrabold text-text-primary mt-0.5">{result.decision.selected_model_name}</h4>
                    <p className="text-xs text-text-muted mt-0.5">ID: {result.decision.selected_model} • Provider: {result.decision.provider}</p>
                  </div>
                  <div className="flex items-center gap-4 text-xs border-t sm:border-t-0 sm:border-l border-border-subtle pt-2 sm:pt-0 sm:pl-4">
                    <div>
                      <span className="text-text-muted text-[10px] block">Est. Latency</span>
                      <span className="font-bold text-accent-primary">{result.decision.estimated_latency_ms.toFixed(0)}ms</span>
                    </div>
                    <div>
                      <span className="text-text-muted text-[10px] block">Est. Cost</span>
                      <span className="font-bold text-accent-success">${result.decision.estimated_cost_usd.toFixed(6)}</span>
                    </div>
                  </div>
                </div>

                {/* Decision Factors */}
                <div className="space-y-2 pt-1 font-mono">
                  <span className="text-xs text-text-muted uppercase tracking-wider font-bold">Decision Factors:</span>
                  <div className="space-y-1.5 text-xs">
                    {result.decision.reasons.map((r, idx) => (
                      <div key={idx} className="flex items-start gap-2.5 text-text-primary p-1.5 rounded-lg bg-bg-primary/40 border border-border-subtle/30">
                        <span className="text-accent-success font-bold">✓</span>
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Rejected Candidates */}
                {Object.keys(result.decision.rejected_candidates || {}).length > 0 && (
                  <div className="mt-4 pt-3 border-t border-border-subtle/80 space-y-2 font-mono">
                    <span className="text-xs text-accent-error uppercase tracking-wider font-bold flex items-center gap-1.5">
                      <XCircle className="w-3.5 h-3.5" /> Pruned / Ineligible Candidates:
                    </span>
                    <div className="space-y-1.5 text-[11px] text-text-muted">
                      {Object.entries(result.decision.rejected_candidates).map(([id, reason]) => (
                        <div key={id} className="p-2 rounded-lg bg-bg-primary/60 border border-border-subtle/40">
                          <span className="font-bold text-text-primary">{id}:</span> {reason}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

            </div>
          )}

          {/* TAB 2: Model Response Stream */}
          {activeTab === 'response' && result.response && (
            <div className="rounded-2xl glass-panel p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle/80 pb-4 font-mono">
                <div>
                  <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-accent-primary" />
                    Response from {result.response.model} ({result.response.provider})
                  </h3>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-text-muted mt-1.5">
                    <span>Latency: <strong className="text-text-primary">{result.metrics?.total_latency_ms || result.response.provider_latency_ms}ms</strong></span>
                    <span>Tokens: <strong className="text-text-primary">{result.response.total_tokens}</strong> ({result.response.input_tokens} in / {result.response.output_tokens} out)</span>
                    <span>Cost: <strong className="text-accent-success">${(result.metrics?.estimated_cost_usd || 0).toFixed(6)}</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {/* Copy button */}
                  <button
                    onClick={copyResponse}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-primary text-text-muted hover:text-text-primary text-xs font-mono"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-accent-success" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>

                  {/* Useful feedback */}
                  <div className="flex items-center gap-1.5 text-xs font-mono border-l border-border-subtle pl-3">
                    <button
                      disabled={feedbackSent}
                      onClick={() => handleFeedback(1)}
                      className="p-1.5 rounded-lg border border-border-subtle bg-bg-primary text-text-muted hover:text-accent-success hover:border-accent-success transition-all disabled:opacity-50"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      disabled={feedbackSent}
                      onClick={() => handleFeedback(-1)}
                      className="p-1.5 rounded-lg border border-border-subtle bg-bg-primary text-text-muted hover:text-accent-error hover:border-accent-error transition-all disabled:opacity-50"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Markdown / Text body */}
              <div className="p-5 rounded-xl bg-bg-primary/95 border border-border-subtle font-mono text-xs text-text-primary whitespace-pre-wrap leading-relaxed shadow-inner">
                {result.response.content}
              </div>
            </div>
          )}

          {/* TAB 3: Candidate Scoreboard */}
          {activeTab === 'candidates' && (
            <div className="rounded-2xl glass-panel p-6 space-y-4 overflow-x-auto">
              <h3 className="font-mono text-xs font-bold text-text-primary uppercase tracking-wider">
                Multi-Criteria Candidate Scoreboard (Normalized 0 - 100 Scale)
              </h3>
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-border-subtle text-text-muted">
                    <th className="pb-3">Candidate Model</th>
                    <th className="pb-3">Provider</th>
                    <th className="pb-3">Tier</th>
                    <th className="pb-3">Overall Score</th>
                    <th className="pb-3">Quality</th>
                    <th className="pb-3">Speed</th>
                    <th className="pb-3">Cost Eff.</th>
                    <th className="pb-3">Capability</th>
                    <th className="pb-3">Eligibility</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle/30">
                  {result.decision.candidate_scores.map((c) => {
                    const isSelected = c.model_id === result.decision.selected_model;
                    return (
                      <tr key={c.model_id} className={`transition-colors ${isSelected ? 'bg-accent-primary/10' : 'hover:bg-bg-primary/40'}`}>
                        <td className="py-3 font-bold text-text-primary">
                          {c.model_name}
                          {isSelected && <span className="ml-2 px-1.5 py-0.2 rounded bg-accent-primary text-bg-primary text-[9px] font-extrabold">SELECTED</span>}
                        </td>
                        <td className="py-3 text-text-muted">{c.provider}</td>
                        <td className="py-3">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                            c.tier === 'POWER' ? 'text-purple-400 bg-purple-500/10' : (c.tier === 'BALANCED' ? 'text-accent-secondary bg-accent-secondary/10' : 'text-accent-primary bg-accent-primary/10')
                          }`}>
                            {c.tier}
                          </span>
                        </td>
                        <td className="py-3 font-bold text-accent-primary text-sm">{c.overall_score.toFixed(1)}</td>
                        <td className="py-3 text-text-muted">{c.quality_component}%</td>
                        <td className="py-3 text-text-muted">{c.speed_component}%</td>
                        <td className="py-3 text-text-muted">{c.cost_component}%</td>
                        <td className="py-3 text-text-muted">{c.capability_component}%</td>
                        <td className="py-3">
                          <span className="text-accent-success font-bold text-[11px] flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Eligible
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
