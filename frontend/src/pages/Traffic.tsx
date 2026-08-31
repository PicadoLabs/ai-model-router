import React, { useEffect, useState } from 'react';
import { Radio, RefreshCw, Layers, Clock, DollarSign, Cpu } from 'lucide-react';
import { fetchApi } from '../lib/api';
import { TrafficItem } from '../types';

export const Traffic: React.FC = () => {
  const [traffic, setTraffic] = useState<TrafficItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTraffic = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<TrafficItem[]>('/api/traffic?limit=50');
      setTraffic(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTraffic();
    const eventSource = new EventSource('http://localhost:8000/api/traffic/stream');
    eventSource.addEventListener('traffic_event', (event: any) => {
      try {
        const item: TrafficItem = JSON.parse(event.data);
        setTraffic((prev) => [item, ...prev.slice(0, 49)]);
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
      <div className="flex items-center justify-between border-b border-border-subtle pb-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-text-primary tracking-wide flex items-center gap-2">
            <Radio className="w-5 h-5 text-accent-primary animate-pulse" />
            LIVE TRAFFIC & TELEMETRY STREAM
          </h2>
          <p className="text-xs text-text-muted font-mono mt-1">
            Real-time feed of all incoming AI requests, latency breakdowns, and selected model destinations.
          </p>
        </div>

        <button
          onClick={loadTraffic}
          className="p-2 rounded-lg border border-border-subtle bg-bg-card text-text-muted hover:text-text-primary font-mono text-xs flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      <div className="rounded-xl border border-border-subtle bg-bg-card p-5 space-y-4 overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-border-subtle text-text-muted">
              <th className="pb-2.5">Time</th>
              <th className="pb-2.5">Request ID</th>
              <th className="pb-2.5">Task</th>
              <th className="pb-2.5">Prompt Extract</th>
              <th className="pb-2.5">Destination Model</th>
              <th className="pb-2.5">Total Latency</th>
              <th className="pb-2.5">Cost (USD)</th>
              <th className="pb-2.5">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle/40">
            {traffic.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-6 text-center text-text-muted">
                  No traffic records available. Run prompts from the Playground or CLI to see live events.
                </td>
              </tr>
            ) : (
              traffic.map((t) => (
                <tr key={t.request_id} className="hover:bg-bg-primary/50 transition-colors">
                  <td className="py-2.5 text-text-muted">
                    {t.timestamp ? t.timestamp.split('T')[1]?.slice(0, 8) : 'N/A'}
                  </td>
                  <td className="py-2.5 text-text-dim text-[11px]">{t.request_id}</td>
                  <td className="py-2.5">
                    <span className="px-1.5 py-0.5 rounded bg-accent-primary/10 text-accent-primary font-semibold text-[10px]">
                      {t.task_type}
                    </span>
                  </td>
                  <td className="py-2.5 text-text-primary max-w-xs truncate" title={t.prompt}>
                    "{t.prompt}"
                  </td>
                  <td className="py-2.5 font-bold text-accent-secondary">
                    {t.selected_model}
                  </td>
                  <td className="py-2.5 text-text-primary font-semibold">
                    {t.total_latency_ms?.toFixed(0)}ms
                  </td>
                  <td className="py-2.5 text-accent-success font-semibold">
                    ${(t.estimated_cost || 0).toFixed(6)}
                  </td>
                  <td className="py-2.5">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                      t.status === 'SUCCESS' ? 'bg-accent-success/20 text-accent-success' : 'bg-accent-secondary/20 text-accent-secondary'
                    }`}>
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
