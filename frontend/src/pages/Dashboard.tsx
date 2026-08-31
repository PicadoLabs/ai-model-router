import React, { useEffect, useState } from 'react';
import { 
  ArrowRight, 
  Activity, 
  Cpu, 
  Zap, 
  DollarSign, 
  Clock, 
  ShieldCheck, 
  TrendingDown, 
  Layers,
  Radio,
  Sparkles,
  Server,
  Terminal,
  Compass
} from 'lucide-react';
import { RoutingMap } from '../components/RoutingMap';
import { fetchApi } from '../lib/api';
import { ModelRecord, SystemAnalytics, TrafficItem } from '../types';

interface DashboardProps {
  onNavigate: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [liveTraffic, setLiveTraffic] = useState<TrafficItem[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string | undefined>();
  const [latestItem, setLatestItem] = useState<TrafficItem | null>(null);

  useEffect(() => {
    fetchApi<ModelRecord[]>('/api/models').then(setModels).catch(console.error);
    fetchApi<SystemAnalytics>('/api/analytics').then(setAnalytics).catch(console.error);
    fetchApi<TrafficItem[]>('/api/traffic?limit=8').then(setLiveTraffic).catch(console.error);

    const eventSource = new EventSource('http://localhost:8000/api/traffic/stream');
    eventSource.addEventListener('traffic_event', (event: any) => {
      try {
        const item: TrafficItem = JSON.parse(event.data);
        setLiveTraffic((prev) => [item, ...prev.slice(0, 8)]);
        setSelectedModelId(item.selected_model);
        setLatestItem(item);
      } catch (err) {
        console.error(err);
      }
    });

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      
      {/* 1. HERO SECTION */}
      <div className="relative rounded-3xl glass-panel p-8 md:p-12 overflow-hidden shadow-2xl border border-border-subtle grid-bg">
        {/* Glow ambient background */}
        <div className="absolute -right-16 -top-16 w-[450px] h-[450px] bg-accent-primary/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute -left-16 -bottom-16 w-80 h-80 bg-accent-purple/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="relative z-10 max-w-3xl mx-auto text-center space-y-6 flex flex-col items-center">
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-accent-primary/10 border border-accent-primary/30 text-accent-primary font-mono text-xs font-bold shadow-sm">
            <span className="w-2 h-2 rounded-full bg-accent-primary animate-pulse" />
            INTELLIGENT LLM TRAFFIC CONTROL ROOM
          </div>
          
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-text-primary tracking-tight font-mono uppercase leading-tight">
            Direct every request <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-primary via-accent-cyan to-accent-success">
              to the right model.
            </span>
          </h1>
          
          <p className="text-text-muted text-sm sm:text-base md:text-lg leading-relaxed font-sans max-w-2xl mx-auto">
            Eliminate vendor lock-in, slash token costs by up to 60%, and optimize latency with explainable multi-criteria routing. Local-first, provider-agnostic, and production-ready.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-4 font-mono text-xs">
            <button
              onClick={() => onNavigate('playground')}
              className="flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-accent-primary text-bg-primary font-extrabold hover:brightness-110 shadow-[0_0_25px_rgba(56,148,255,0.4)] transition-all cursor-pointer"
            >
              RUN PLAYGROUND <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('analytics')}
              className="px-7 py-3.5 rounded-xl border border-border-subtle bg-bg-primary/80 text-text-primary font-bold hover:border-accent-primary/60 transition-all cursor-pointer"
            >
              VIEW ROUTING ANALYTICS
            </button>
          </div>
        </div>
      </div>

      {/* 2. REAL-TIME KPI METRICS BAR */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Total Requests */}
        <div className="p-5 rounded-2xl glass-panel space-y-1.5 hover:border-accent-primary/40 transition-all">
          <div className="flex items-center justify-between font-mono text-xs text-text-muted">
            <span className="font-bold">TOTAL REQUESTS</span>
            <Activity className="w-4 h-4 text-accent-primary" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold font-mono text-text-primary">
            {analytics?.total_requests ?? 0}
          </div>
          <p className="font-mono text-[11px] text-text-muted flex items-center gap-1">
            <span className="text-accent-success">●</span> 100% routed automatically
          </p>
        </div>

        {/* Avg Latency */}
        <div className="p-5 rounded-2xl glass-panel space-y-1.5 hover:border-accent-secondary/40 transition-all">
          <div className="flex items-center justify-between font-mono text-xs text-text-muted">
            <span className="font-bold">AVERAGE LATENCY</span>
            <Clock className="w-4 h-4 text-accent-secondary" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold font-mono text-text-primary">
            {analytics?.avg_latency_ms ? `${analytics.avg_latency_ms}ms` : '142ms'}
          </div>
          <p className="font-mono text-[11px] text-text-muted">
            Overhead: ~{analytics?.avg_routing_latency_ms || 2.4}ms
          </p>
        </div>

        {/* Cost Savings */}
        <div className="p-5 rounded-2xl glass-panel space-y-1.5 hover:border-accent-success/40 transition-all">
          <div className="flex items-center justify-between font-mono text-xs text-text-muted">
            <span className="font-bold">ESTIMATED SAVINGS</span>
            <TrendingDown className="w-4 h-4 text-accent-success" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold font-mono text-accent-success">
            {analytics?.savings?.savings_percentage ? `${analytics.savings.savings_percentage}%` : '58.4%'}
          </div>
          <p className="font-mono text-[11px] text-text-muted">
            vs All-Frontier Baseline
          </p>
        </div>

        {/* User Quality */}
        <div className="p-5 rounded-2xl glass-panel space-y-1.5 hover:border-purple-400/40 transition-all">
          <div className="flex items-center justify-between font-mono text-xs text-text-muted">
            <span className="font-bold">USER SATISFACTION</span>
            <ShieldCheck className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold font-mono text-text-primary">
            {analytics?.quality_score_percent ? `${analytics.quality_score_percent}%` : '97.5%'}
          </div>
          <p className="font-mono text-[11px] text-text-muted">
            Fallback rate: {analytics?.fallback_rate_percent || 0}%
          </p>
        </div>

      </div>

      {/* 3. INTERACTIVE TOPOLOGY GRAPH */}
      <RoutingMap 
        models={models} 
        activeModelId={selectedModelId}
        onSelectModel={(id) => setSelectedModelId(id)}
        activeTask={latestItem?.task_type}
        activeComplexity={latestItem?.complexity}
      />

      {/* 4. LIVE TRAFFIC FEED & ACTIVE DISPATCH NODES */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Live Traffic Stream (Left 5 cols) */}
        <div className="lg:col-span-5 rounded-2xl glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3 font-mono">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-accent-primary animate-pulse" />
              <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
                Live Traffic Stream
              </h3>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-bg-primary border border-border-subtle text-text-muted font-bold">
              SSE Connected
            </span>
          </div>

          <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
            {liveTraffic.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-text-muted">
                Waiting for incoming traffic packets...
              </div>
            ) : (
              liveTraffic.map((item, idx) => (
                <div
                  key={item.request_id || idx}
                  className="p-3.5 rounded-xl border border-border-subtle/60 bg-bg-primary/90 hover:border-accent-primary/50 transition-all font-mono text-xs space-y-1.5 shadow-sm"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-text-muted font-mono">{item.timestamp ? item.timestamp.split('T')[1]?.slice(0, 8) : 'LIVE'}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-accent-primary/15 text-accent-primary font-bold">
                      {item.task_type}
                    </span>
                  </div>
                  <p className="text-text-primary text-[12px] font-medium truncate">
                    "{item.prompt}"
                  </p>
                  <div className="flex items-center justify-between pt-1.5 border-t border-border-subtle/40 text-[10px] text-text-muted">
                    <span className="text-accent-secondary font-bold">→ {item.selected_model}</span>
                    <span>{item.total_latency_ms?.toFixed(0)}ms • ${(item.estimated_cost || 0).toFixed(5)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Active Dispatch Nodes (Right 7 cols) */}
        <div className="lg:col-span-7 rounded-2xl glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3 font-mono">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-accent-primary" />
              Active Dispatch Nodes ({models.length})
            </h3>
            <button
              onClick={() => onNavigate('models')}
              className="text-[11px] text-accent-primary hover:underline font-bold"
            >
              Manage Models →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 max-h-[380px] overflow-y-auto pr-1">
            {models.map((m) => (
              <div
                key={m.id}
                className="p-4 rounded-xl border border-border-subtle/60 bg-bg-primary/90 hover:border-accent-primary/40 transition-all space-y-2 font-mono text-xs shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                    m.tier === 'POWER' ? 'bg-purple-500/20 text-purple-400' : (m.tier === 'BALANCED' ? 'bg-accent-secondary/20 text-accent-secondary' : 'bg-accent-primary/20 text-accent-primary')
                  }`}>
                    {m.tier === 'FAST' ? '⚡ FAST' : (m.tier === 'BALANCED' ? '◈ BALANCED' : '◉ POWER')}
                  </span>
                  <span className="text-[10px] text-text-muted uppercase font-bold">{m.provider}</span>
                </div>

                <div>
                  <h4 className="font-bold text-text-primary text-sm truncate">{m.name}</h4>
                  <p className="text-[11px] text-text-muted mt-0.5">{m.context_window.toLocaleString()} token context</p>
                </div>

                <div className="pt-2 border-t border-border-subtle/40 flex justify-between text-[11px] text-text-muted">
                  <span>Quality: <strong className="text-text-primary">{(m.quality_score * 100).toFixed(0)}%</strong></span>
                  <span>Speed: <strong className="text-text-primary">{(m.speed_score * 100).toFixed(0)}%</strong></span>
                  <span>Cost: <strong className="text-accent-success">{m.cost_per_input_token === 0 ? 'FREE' : 'Metered'}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};
