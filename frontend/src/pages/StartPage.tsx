import React, { useState } from 'react';
import { 
  Terminal, 
  Copy, 
  Check, 
  ArrowRight, 
  Code2, 
  Cpu, 
  Layers, 
  Zap, 
  BookOpen, 
  Sparkles, 
  Bot, 
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

interface StartPageProps {
  onNavigate: (tab: string) => void;
}

export const StartPage: React.FC<StartPageProps> = ({ onNavigate }) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<'cost' | 'speed' | 'quality' | 'bandit'>('cost');
  const [selectedLang, setSelectedLang] = useState<'python' | 'curl' | 'ts' | 'langchain'>('python');

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getSnippets = () => {
    if (selectedLang === 'python') {
      return `# 1. Install CLI & SDK
# pip install model-router-cli

from modelrouter import ModelRouterClient

client = ModelRouterClient(
    base_url="http://localhost:8000",
    strategy="${selectedStrategy === 'cost' ? 'cost_optimized' : selectedStrategy === 'speed' ? 'speed_optimized' : selectedStrategy === 'quality' ? 'quality_optimized' : 'thompson_sampling'}"
)

# Route query automatically
result = client.route(
    prompt="Write an async background queue processor in Rust.",
    max_latency_ms=1200
)

print(f"Target Model: {result.selected_model}")
print(f"Cost Savings: {result.cost_savings_pct}%")
print(result.content)`;
    }

    if (selectedLang === 'curl') {
      return `# Send standard OpenAI-compatible JSON payload to Model Router
curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer mr_live_key" \\
  -d '{
    "model": "${selectedStrategy === 'cost' ? 'cost-first' : selectedStrategy === 'speed' ? 'latency-first' : 'quality-first'}",
    "messages": [
      {"role": "user", "content": "Explain vector search indexing in PostgreSQL pgvector."}
    ]
  }'`;
    }

    if (selectedLang === 'ts') {
      return `// TypeScript / Node.js with OpenAI SDK
import OpenAI from 'openai';

const router = new OpenAI({
  baseURL: 'http://localhost:8000/v1',
  apiKey: process.env.MODEL_ROUTER_API_KEY || 'mr_live_key'
});

async function run() {
  const res = await router.chat.completions.create({
    model: '${selectedStrategy === 'cost' ? 'auto' : 'quality-first'}',
    messages: [{ role: 'user', content: 'Generate schema migration script.' }]
  });

  console.log('Selected:', res.model);
  console.log(res.choices[0].message.content);
}

run();`;
    }

    return `# LangChain Integration
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="mr_live_key",
    model="auto"  # Model Router intercepts and routes intelligently
)

response = llm.invoke("Summarize the architectural principles of Paxos.")
print(response.content)`;
  };

  return (
    <div className="max-w-5xl mx-auto space-y-16 pb-20 pt-4">
      
      {/* Hero */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <h1 className="text-3xl sm:text-[44px] font-bold text-text-primary tracking-tight leading-[1.15]">
          Get started with Model Router
        </h1>

        <p className="text-[15px] text-text-muted leading-relaxed">
          Model Router is a place to start learning, too. Explore practical guides and drop-in code templates for using intelligent routing in everyday work, one step at a time.
        </p>
      </div>

      {/* 3 Pathway Cards (Matching Image 5) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Card 1 */}
        <div className="rounded-2xl glass-panel border border-border-subtle bg-bg-card p-6 sm:p-7 flex flex-col justify-between hover:border-accent-primary/60 transition-all space-y-6">
          <div className="space-y-3">
            <div className="w-9 h-9 rounded-xl bg-accent-primary/10 border border-accent-primary/30 text-accent-primary flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-text-primary">
              Start with the basics
            </h3>
            <p className="text-xs text-text-muted leading-relaxed">
              "Where do I even start?" Start with how Model Router evaluates token counts, context complexity, and cost tiers before calling an LLM.
            </p>
          </div>

          <button
            onClick={() => onNavigate('playground')}
            className="text-xs font-mono font-bold text-accent-primary hover:underline flex items-center gap-1.5 cursor-pointer"
          >
            <span>Meet the router playground</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Card 2 */}
        <div className="rounded-2xl glass-panel border border-border-subtle bg-bg-card p-6 sm:p-7 flex flex-col justify-between hover:border-accent-purple/60 transition-all space-y-6">
          <div className="space-y-3">
            <div className="w-9 h-9 rounded-xl bg-accent-purple/10 border border-accent-purple/30 text-accent-purple flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-text-primary">
              Work better together
            </h3>
            <p className="text-xs text-text-muted leading-relaxed">
              "I'm getting the hang of this!" Set up multi-tenant workspaces, enforce rate limits per team, and inspect live Prometheus telemetry.
            </p>
          </div>

          <button
            onClick={() => onNavigate('settings')}
            className="text-xs font-mono font-bold text-accent-purple hover:underline flex items-center gap-1.5 cursor-pointer"
          >
            <span>Configure workspaces & keys</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Card 3 */}
        <div className="rounded-2xl glass-panel border border-border-subtle bg-bg-card p-6 sm:p-7 flex flex-col justify-between hover:border-accent-success/60 transition-all space-y-6">
          <div className="space-y-3">
            <div className="w-9 h-9 rounded-xl bg-accent-success/10 border border-accent-success/30 text-accent-success flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-text-primary">
              Make a rule of your own
            </h3>
            <p className="text-xs text-text-muted leading-relaxed">
              "I could turn this into a rule!" Create deterministic keyword or regex routing rules that override the classifier for domain compliance.
            </p>
          </div>

          <button
            onClick={() => onNavigate('rules')}
            className="text-xs font-mono font-bold text-accent-success hover:underline flex items-center gap-1.5 cursor-pointer"
          >
            <span>Create custom routing rule</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>

      {/* Interactive Code & Strategy Quickstart Builder */}
      <div className="rounded-2xl glass-panel border border-border-subtle bg-bg-card p-6 sm:p-8 space-y-6 shadow-2xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <Terminal className="w-5 h-5 text-accent-primary" />
              Quick Integration Code Builder
            </h2>
            <p className="text-xs text-text-muted">
              Select your language and routing policy to get instant, drop-in integration code.
            </p>
          </div>

          {/* Language Selector */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-bg-primary border border-border-subtle">
            {(['python', 'curl', 'ts', 'langchain'] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => setSelectedLang(lang)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                  selectedLang === lang
                    ? 'bg-accent-primary text-bg-primary'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                {lang === 'ts' ? 'TypeScript' : lang === 'curl' ? 'cURL' : lang.charAt(0).toUpperCase() + lang.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Strategy Selector Pills */}
        <div className="space-y-2">
          <div className="text-[11px] font-mono font-bold text-text-muted uppercase">
            ROUTING STRATEGY
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { id: 'cost', label: 'Cost-Optimized', desc: 'Up to 90% savings via SLMs' },
              { id: 'speed', label: 'Speed-First', desc: 'Sub-300ms latency SLA' },
              { id: 'quality', label: 'Quality-First', desc: 'Frontier reasoning focus' },
              { id: 'bandit', label: 'Thompson Bandit', desc: 'Adaptive online learning' }
            ].map((strat) => (
              <button
                key={strat.id}
                onClick={() => setSelectedStrategy(strat.id as any)}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  selectedStrategy === strat.id
                    ? 'bg-accent-primary/10 border-accent-primary text-text-primary'
                    : 'bg-bg-primary/50 border-border-subtle text-text-muted hover:border-border-active'
                }`}
              >
                <div className="text-xs font-bold">{strat.label}</div>
                <div className="text-[10px] text-text-dim mt-0.5">{strat.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Code Snippet Box */}
        <div className="relative rounded-xl bg-black/90 border border-border-subtle p-5 font-mono text-xs text-green-400 overflow-x-auto">
          <button
            onClick={() => copyToClipboard(getSnippets(), 'builder-copy')}
            className="absolute right-4 top-4 px-3 py-1.5 rounded-lg bg-bg-secondary border border-border-subtle text-xs text-text-muted hover:text-text-primary flex items-center gap-1.5 cursor-pointer"
          >
            {copiedId === 'builder-copy' ? <Check className="w-3.5 h-3.5 text-accent-success" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedId === 'builder-copy' ? 'Copied to clipboard' : 'Copy Code'}</span>
          </button>
          <pre className="pt-2 leading-relaxed">
            <code>{getSnippets()}</code>
          </pre>
        </div>

        {/* Actions Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between pt-2 gap-4 text-xs font-mono">
          <div className="flex items-center gap-2 text-text-muted">
            <CheckCircle2 className="w-4 h-4 text-accent-success" />
            <span>Ready for production • Tested with Python 3.10+ and Node.js 18+</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('docs')}
              className="px-4 py-2 rounded-xl bg-bg-secondary border border-border-subtle text-text-primary font-bold hover:bg-bg-primary cursor-pointer"
            >
              Read Full Docs
            </button>
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-4 py-2 rounded-xl bg-accent-primary text-bg-primary font-bold hover:brightness-110 cursor-pointer"
            >
              Open Control Room →
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};
