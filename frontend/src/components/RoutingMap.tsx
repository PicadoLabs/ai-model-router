import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Cpu, 
  Sparkles, 
  ArrowRight, 
  Radio, 
  Activity, 
  ShieldCheck,
  CheckCircle2,
  Server,
  Layers
} from 'lucide-react';
import { ModelRecord } from '../types';

interface RoutingMapProps {
  models: ModelRecord[];
  activeModelId?: string;
  onSelectModel?: (modelId: string) => void;
  activeTask?: string;
  activeComplexity?: number;
}

export const RoutingMap: React.FC<RoutingMapProps> = ({ 
  models, 
  activeModelId, 
  onSelectModel,
  activeTask,
  activeComplexity
}) => {
  const [pulseSignal, setPulseSignal] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseSignal((p) => (p + 1) % 100);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const fastModels = models.filter((m) => m.tier === 'FAST');
  const balancedModels = models.filter((m) => m.tier === 'BALANCED');
  const powerModels = models.filter((m) => m.tier === 'POWER');

  // Determine active tier based on selected model
  const activeModel = models.find(m => m.id === activeModelId);
  const activeTier = activeModel?.tier || 'BALANCED';

  return (
    <div className="relative w-full rounded-2xl glass-panel p-6 sm:p-8 overflow-hidden shadow-2xl border border-border-subtle grid-bg">
      
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-accent-primary/5 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-0 right-0 w-80 h-80 bg-accent-purple/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Header bar */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8 pb-4 border-b border-border-subtle/80">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-primary/10 border border-accent-primary/30 flex items-center justify-center text-accent-primary shadow-[0_0_15px_rgba(56,148,255,0.2)]">
            <Radio className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-mono text-sm font-extrabold tracking-wider text-text-primary uppercase">
                AI Traffic Dispatch Topology Map
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent-success/15 border border-accent-success/30 text-accent-success font-mono font-bold">
                LIVE INTERCEPT
              </span>
            </div>
            <p className="text-[11px] text-text-muted font-mono mt-0.5">
              Deterministic Ingress • Multi-Criteria Matrix • Zero-Lockin Egress
            </p>
          </div>
        </div>

        {/* Live stats capsule */}
        <div className="flex items-center gap-4 font-mono text-xs">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-primary/80 border border-border-subtle text-text-muted">
            <span className="text-[10px] text-text-dim uppercase">Overhead:</span>
            <span className="text-text-primary font-bold">2.4ms</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-primary/80 border border-border-subtle text-text-muted">
            <span className="text-[10px] text-text-dim uppercase">Local Routing:</span>
            <span className="text-accent-success font-bold">100% Free</span>
          </div>
        </div>
      </div>

      {/* Interactive Topology Graph */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        {/* 1. Ingress Lane (Left 3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-text-muted px-1">
            <span className="flex items-center gap-1.5 text-text-primary font-bold">
              <Activity className="w-3.5 h-3.5 text-accent-primary" /> INGRESS LANE
            </span>
            <span className="text-[10px] text-accent-primary animate-pulse font-mono">STREAMING</span>
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            {/* Packet 1 */}
            <div className={`p-3 rounded-xl border transition-all duration-300 ${
              activeTask === 'DEBUGGING' || !activeTask
                ? 'bg-bg-card border-accent-primary/60 shadow-[0_0_20px_rgba(56,148,255,0.12)]' 
                : 'bg-bg-primary/60 border-border-subtle opacity-70'
            }`}>
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-text-muted">DEBUGGING</span>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-accent-secondary/20 text-accent-secondary font-bold">
                  HIGH 0.82
                </span>
              </div>
              <p className="text-text-primary text-[12px] font-medium truncate">
                "Debug async scheduler deadlock"
              </p>
              <div className="mt-2 pt-2 border-t border-border-subtle/40 flex justify-between text-[10px] text-text-dim">
                <span>Tokens: ~420</span>
                <span className="text-accent-primary font-semibold">Priority: Reasoning</span>
              </div>
            </div>

            {/* Packet 2 */}
            <div className={`p-3 rounded-xl border transition-all duration-300 ${
              activeTask === 'CODING' 
                ? 'bg-bg-card border-accent-primary/60 shadow-[0_0_20px_rgba(56,148,255,0.12)]' 
                : 'bg-bg-primary/60 border-border-subtle opacity-70'
            }`}>
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-text-muted">CODING</span>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-accent-success/20 text-accent-success font-bold">
                  LOW 0.35
                </span>
              </div>
              <p className="text-text-primary text-[12px] font-medium truncate">
                "Write Python JSON parser function"
              </p>
              <div className="mt-2 pt-2 border-t border-border-subtle/40 flex justify-between text-[10px] text-text-dim">
                <span>Tokens: ~95</span>
                <span className="text-accent-success font-semibold">Priority: Speed</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Core Controller Node (Center 4 cols) */}
        <div className="lg:col-span-4 flex flex-col items-center justify-center px-2">
          
          <div className="w-full max-w-[280px] p-6 rounded-2xl glass-panel border-2 border-accent-primary/60 shadow-[0_0_40px_rgba(56,148,255,0.2)] text-center relative group backdrop-blur-xl">
            
            {/* Pulsing badge */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-accent-primary text-bg-primary font-mono text-[10px] font-extrabold tracking-wider uppercase shadow-[0_0_12px_rgba(56,148,255,0.6)]">
              MODEL ROUTER CORE
            </div>

            {/* Glowing Icon Hub */}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-b from-accent-primary/20 to-accent-primary/5 border border-accent-primary/40 mx-auto flex items-center justify-center text-accent-primary mb-4 shadow-[inset_0_0_20px_rgba(56,148,255,0.2)]">
              <Zap className="w-8 h-8 animate-pulse text-accent-primary" />
            </div>

            <h4 className="font-mono text-base font-bold text-text-primary tracking-wide">
              MULTI-CRITERIA ENGINE
            </h4>
            <p className="font-mono text-xs text-text-muted mt-1">
              Quality • Latency • Cost • Caps
            </p>

            {/* Real-time policy metrics matrix */}
            <div className="mt-4 pt-4 border-t border-border-subtle/80 grid grid-cols-3 gap-2 font-mono text-[11px]">
              <div className="p-1.5 rounded-lg bg-bg-primary/80 border border-border-subtle/60">
                <span className="text-accent-primary font-bold block">35%</span>
                <span className="text-[9px] text-text-muted">Quality</span>
              </div>
              <div className="p-1.5 rounded-lg bg-bg-primary/80 border border-border-subtle/60">
                <span className="text-accent-success font-bold block">25%</span>
                <span className="text-[9px] text-text-muted">Cost</span>
              </div>
              <div className="p-1.5 rounded-lg bg-bg-primary/80 border border-border-subtle/60">
                <span className="text-accent-secondary font-bold block">20%</span>
                <span className="text-[9px] text-text-muted">Speed</span>
              </div>
            </div>

          </div>

        </div>

        {/* 3. Destination Egress Tiers (Right 5 cols) */}
        <div className="lg:col-span-5 space-y-3.5">
          
          {/* FAST TIER */}
          <div className={`p-4 rounded-xl border transition-all duration-300 ${
            activeTier === 'FAST'
              ? 'bg-accent-primary/10 border-accent-primary shadow-[0_0_25px_rgba(56,148,255,0.18)]'
              : 'glass-panel border-border-subtle hover:border-accent-primary/40'
          }`}>
            <div className="flex items-center justify-between font-mono text-xs mb-2">
              <div className="flex items-center gap-2 font-bold text-accent-primary">
                <Zap className="w-4 h-4" />
                <span>⚡ FAST TIER</span>
              </div>
              <span className="text-[11px] text-text-muted font-mono">&lt; 150ms • High Throughput</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {fastModels.map((m) => {
                const isSelected = activeModelId === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => onSelectModel?.(m.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-accent-primary text-bg-primary border-accent-primary font-bold shadow-[0_0_12px_rgba(56,148,255,0.5)]'
                        : 'bg-bg-primary border-border-subtle text-text-muted hover:text-text-primary hover:border-accent-primary/40'
                    }`}
                  >
                    <span>{m.name}</span>
                    {m.cost_per_input_token === 0 && (
                      <span className="text-[9px] px-1 rounded bg-accent-success/20 text-accent-success font-bold">
                        FREE
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* BALANCED TIER */}
          <div className={`p-4 rounded-xl border transition-all duration-300 ${
            activeTier === 'BALANCED'
              ? 'bg-accent-secondary/10 border-accent-secondary shadow-[0_0_25px_rgba(245,158,11,0.18)]'
              : 'glass-panel border-border-subtle hover:border-accent-secondary/40'
          }`}>
            <div className="flex items-center justify-between font-mono text-xs mb-2">
              <div className="flex items-center gap-2 font-bold text-accent-secondary">
                <Cpu className="w-4 h-4" />
                <span>◈ BALANCED TIER</span>
              </div>
              <span className="text-[11px] text-text-muted font-mono">General QA • Coding & Analytics</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {balancedModels.map((m) => {
                const isSelected = activeModelId === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => onSelectModel?.(m.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-accent-secondary text-bg-primary border-accent-secondary font-bold shadow-[0_0_12px_rgba(245,158,11,0.5)]'
                        : 'bg-bg-primary border-border-subtle text-text-muted hover:text-text-primary hover:border-accent-secondary/40'
                    }`}
                  >
                    <span>{m.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* POWER TIER */}
          <div className={`p-4 rounded-xl border transition-all duration-300 ${
            activeTier === 'POWER'
              ? 'bg-purple-500/15 border-purple-500 shadow-[0_0_25px_rgba(139,92,246,0.22)]'
              : 'glass-panel border-border-subtle hover:border-purple-500/40'
          }`}>
            <div className="flex items-center justify-between font-mono text-xs mb-2">
              <div className="flex items-center gap-2 font-bold text-purple-400">
                <Sparkles className="w-4 h-4" />
                <span>◉ POWER TIER</span>
              </div>
              <span className="text-[11px] text-text-muted font-mono">Deep Reasoning • Frontier Models</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {powerModels.map((m) => {
                const isSelected = activeModelId === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => onSelectModel?.(m.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-purple-500 text-white border-purple-400 font-bold shadow-[0_0_15px_rgba(139,92,246,0.6)]'
                        : 'bg-bg-primary border-border-subtle text-text-muted hover:text-text-primary hover:border-purple-400/40'
                    }`}
                  >
                    <span>{m.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
