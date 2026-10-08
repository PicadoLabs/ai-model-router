import React, { useState } from 'react';
import { 
  ArrowRight, 
  ChevronLeft, 
  ChevronRight, 
  Check, 
  Zap, 
  TrendingDown, 
  Layers, 
  Code2, 
  FileText, 
  Bot,
  Activity,
} from 'lucide-react';
import { ProviderIconMap } from '../components/ProviderLogos';

interface Scenario {
  title: string;
  userQuery: string;
  userQuote: string;
  routerAction: string;
  routerPoints: string[];
  routerQuote: string;
  resultTitle: string;
  resultModel: string;
  resultStats: string;
  resultQuote: string;
}

const scenarios: Scenario[] = [
  {
    title: 'A complex coding task arrives',
    userQuery: 'Write an optimized PostgreSQL migration with multi-column indexing and partition triggers for 50M rows.',
    userQuote: '"How do I route this without losing reasoning depth?"',
    routerAction: 'Model Router',
    routerPoints: [
      'Detected CODING + HIGH_COMPLEXITY',
      'Evaluates quality Pareto frontier',
      'Selects frontier reasoning model'
    ],
    routerQuote: '"I\'ve got a policy for this."',
    resultTitle: 'Optimal precision execution',
    resultModel: 'claude-3-5-sonnet',
    resultStats: '1,420ms · $0.0150 · 96.4% accuracy',
    resultQuote: '"Flawless partitioning script delivered!"',
  },
  {
    title: 'A simple FAQ lookup comes in',
    userQuery: 'What is your refund policy for annual enterprise subscriptions cancelled within 14 days?',
    userQuote: '"Why pay $30/1M tokens for simple FAQ lookups?"',
    routerAction: 'Model Router',
    routerPoints: [
      'Detected GENERAL_QA + LOW_COMPLEXITY',
      'Routes to ultra-fast SLM tier',
      'Caches for sub-ms semantic match'
    ],
    routerQuote: '"I\'ve got an 88% cost reduction for this."',
    resultTitle: 'Instant, cost-effective reply',
    resultModel: 'gemini-1.5-flash',
    resultStats: '180ms · $0.0003 · 90% savings',
    resultQuote: '"Exact answer at a fraction of a cent!"',
  },
  {
    title: 'Batch summarization needed',
    userQuery: 'Summarize key action items and deadline deliverables from this 4-page meeting transcript.',
    userQuote: '"I need immediate summarization across 100 parallel chats."',
    routerAction: 'Model Router',
    routerPoints: [
      'Detected SUMMARIZATION + MEDIUM',
      'Dispatches to high-throughput engine',
      'Guarantees <350ms TTFT'
    ],
    routerQuote: '"I\'ve got a speed-first policy for this."',
    resultTitle: 'Blazing fast streaming',
    resultModel: 'deepseek-chat-v3',
    resultStats: '240ms · $0.0012 · 85ms TTFT',
    resultQuote: '"Summary returned before the user finished typing!"',
  },
  {
    title: 'Primary provider goes down',
    userQuery: 'Generate real-time compliance audit checklist for HIPAA healthcare client onboarding.',
    userQuote: '"Primary provider threw 503 Service Unavailable."',
    routerAction: 'Circuit Breaker',
    routerPoints: [
      'Primary upstream returns 503',
      'Circuit breaker trips (<2ms)',
      'Zero-downtime failover to backup'
    ],
    routerQuote: '"I\'ve tripped the breaker and rerouted."',
    resultTitle: 'Zero-downtime resilience',
    resultModel: 'claude-3-5-sonnet (Fallback)',
    resultStats: '0ms downtime · 4ms failover · 200 OK',
    resultQuote: '"End user experienced zero outage!"',
  }
];

interface OverviewProps {
  onNavigate: (tab: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({ onNavigate }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const scenario = scenarios[currentIndex];

  const supportedProviders = [
    'OpenAI', 'Anthropic', 'Google Gemini', 'DeepSeek', 
    'Groq', 'Ollama', 'LangChain', 'LlamaIndex'
  ];

  return (
    <div className="space-y-24 pb-20">
      
      {/* ─── Hero ─── */}
      <section className="text-center max-w-3xl mx-auto pt-8 space-y-5">
        <h1 className="text-3xl sm:text-[44px] font-bold tracking-tight text-text-primary leading-[1.15]">
          Still manually choosing{' '}
          <br className="hidden sm:inline" />
          <span className="text-accent-primary">
            AI models for every request?
          </span>
        </h1>
        
        <p className="text-[15px] text-text-muted max-w-2xl mx-auto leading-relaxed">
          AI Model Router is an open-source library of{' '}
          <strong className="text-text-primary underline underline-offset-2 decoration-accent-primary/40">
            intelligent routing policies
          </strong>{' '}
          across the LLM lifecycle, already used to optimize millions of tokens in production.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
          <span className="text-xs text-text-dim font-medium">Works with</span>
          {supportedProviders.map((p) => {
            const Icon = ProviderIconMap[p];
            return (
              <span
                key={p}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-bg-card border border-border-subtle text-xs font-medium text-text-primary"
              >
                {Icon && <Icon className="w-3.5 h-3.5 opacity-80" />}
                <span>{p}</span>
              </span>
            );
          })}
          <span className="text-xs text-accent-primary font-medium cursor-pointer hover:underline" onClick={() => onNavigate('docs')}>
            and more
          </span>
        </div>
      </section>

      {/* ─── 3-Piece Puzzle Carousel ─── */}
      <section className="relative max-w-5xl mx-auto">
        
        <button
          onClick={() => setCurrentIndex((currentIndex - 1 + scenarios.length) % scenarios.length)}
          className="absolute -left-3 sm:-left-5 top-1/2 -translate-y-1/2 z-20 w-9 h-9 rounded-full bg-bg-card border border-border-subtle hover:border-accent-primary text-text-muted hover:text-text-primary flex items-center justify-center shadow-md transition-colors cursor-pointer"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <button
          onClick={() => setCurrentIndex((currentIndex + 1) % scenarios.length)}
          className="absolute -right-3 sm:-right-5 top-1/2 -translate-y-1/2 z-20 w-9 h-9 rounded-full bg-bg-card border border-border-subtle hover:border-accent-primary text-text-muted hover:text-text-primary flex items-center justify-center shadow-md transition-colors cursor-pointer"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 rounded-2xl overflow-hidden border border-border-subtle shadow-lg">
          
          {/* Card 1: Manual / Input  (warm tone) */}
          <div className="p-6 sm:p-7 bg-[#2F261F] dark:bg-[#241E17] text-[#E8DDD0] flex flex-col justify-between border-b md:border-b-0 md:border-r border-[#4A3D30]/40 min-h-[280px]">
            <div className="space-y-4">
              <h3 className="text-[15px] font-semibold leading-snug">
                {scenario.title}
              </h3>
              <div className="p-3 rounded-lg bg-black/25 border border-white/10 text-[13px] leading-relaxed line-clamp-3">
                "{scenario.userQuery}"
              </div>
            </div>
            <p className="text-[13px] italic opacity-75 pt-5 border-t border-white/10">
              {scenario.userQuote}
            </p>
          </div>

          {/* Card 2: Model Router  (deep blue) */}
          <div className="p-6 sm:p-7 bg-[#1A2A42] dark:bg-[#152236] text-[#C8D8EC] flex flex-col justify-between border-b md:border-b-0 md:border-r border-[#2A4060]/50 min-h-[280px]">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-[15px] font-semibold leading-snug">
                  {scenario.routerAction}
                </h3>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-accent-primary/20 text-accent-primary border border-accent-primary/30">
                  &lt; 1ms
                </span>
              </div>
              <ul className="space-y-2 text-[13px]">
                {scenario.routerPoints.map((p, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-accent-primary shrink-0 mt-0.5" />
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
            <p className="text-[13px] italic opacity-75 pt-5 border-t border-white/10">
              {scenario.routerQuote}
            </p>
          </div>

          {/* Card 3: Result  (green) */}
          <div className="p-6 sm:p-7 bg-[#1A3D30] dark:bg-[#142E24] text-[#C8E8DC] flex flex-col justify-between min-h-[280px]">
            <div className="space-y-4">
              <h3 className="text-[15px] font-semibold leading-snug">
                {scenario.resultTitle}
              </h3>
              <div className="p-3 rounded-lg bg-black/25 border border-white/10 space-y-1.5">
                <div className="text-[13px] font-semibold text-emerald-300">
                  {scenario.resultModel}
                </div>
                <div className="text-[12px] opacity-80">
                  {scenario.resultStats}
                </div>
              </div>
            </div>
            <p className="text-[13px] italic opacity-75 pt-5 border-t border-white/10">
              {scenario.resultQuote}
            </p>
          </div>
        </div>

        {/* Dots */}
        <div className="flex items-center justify-center gap-2 mt-5">
          {scenarios.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentIndex(i)}
              className={`rounded-full transition-all cursor-pointer ${
                i === currentIndex ? 'w-6 h-2.5 bg-accent-primary' : 'w-2.5 h-2.5 bg-border-subtle hover:bg-text-dim'
              }`}
            />
          ))}
        </div>
      </section>

      {/* ─── Cost & Latency Trend ─── */}
      <section className="max-w-4xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Production cost & latency curve
          </h2>
          <p className="text-sm text-text-muted">
            How engineering teams eliminate token waste while maintaining 99%+ accuracy.
          </p>
        </div>

        <div className="rounded-2xl bg-bg-card border border-border-subtle overflow-hidden shadow-md">
          
          {/* Tabs */}
          <div className="grid grid-cols-3 border-b border-border-subtle text-[13px] font-medium">
            {[
              { label: 'Good old days', active: false },
              { label: 'The AI boom', active: false },
              { label: 'Model Router introduced', active: true }
            ].map((tab, i) => (
              <div key={i} className={`py-3 text-center ${
                tab.active
                  ? 'text-accent-success border-b-2 border-accent-success font-semibold bg-bg-card'
                  : 'text-text-muted bg-bg-secondary/50'
              }`}>
                {tab.label}
              </div>
            ))}
          </div>

          {/* Chart */}
          <div className="p-6 sm:p-10">
            <div className="relative h-60 sm:h-72 w-full">
              <svg className="w-full h-full" viewBox="0 0 800 280" fill="none">
                {/* Grid */}
                {[50, 110, 170, 230].map(y => (
                  <line key={y} x1="50" y1={y} x2="740" y2={y} stroke="currentColor" strokeOpacity="0.06" strokeDasharray="4 4" />
                ))}

                {/* Deployment Marker */}
                <line x1="470" y1="20" x2="470" y2="250" stroke="var(--theme-accent-primary, #5B9BF5)" strokeOpacity="0.35" strokeDasharray="3 3" />
                <text x="478" y="34" fill="var(--theme-accent-primary, #5B9BF5)" fontSize="10" fontFamily="sans-serif" fontWeight="600">
                  Model Router Deployed
                </text>

                {/* Savings Area */}
                <path d="M 470 175 Q 590 140 720 100 L 720 235 Q 590 230 470 175 Z" fill="#34A47C" fillOpacity="0.1" />

                {/* Lines */}
                <path d="M 80 225 Q 270 200 470 120 T 720 50" stroke="#D9534F" strokeWidth="2" strokeDasharray="6 4" />
                <path d="M 80 240 Q 270 225 470 175 T 720 100" stroke="#E5A64E" strokeWidth="2.5" />
                <path d="M 80 240 Q 270 225 470 175 Q 560 210 720 235" stroke="#34A47C" strokeWidth="2.5" />

                {/* Points */}
                <circle cx="470" cy="175" r="4" fill="var(--theme-accent-primary, #5B9BF5)" />
                <circle cx="720" cy="50" r="3.5" fill="#D9534F" />
                <circle cx="720" cy="100" r="3.5" fill="#E5A64E" />
                <circle cx="720" cy="235" r="5" fill="#34A47C" />

                {/* Labels */}
                <text x="728" y="55" fill="#D9534F" fontSize="10" fontFamily="sans-serif">Query Volume</text>
                <text x="728" y="105" fill="#E5A64E" fontSize="10" fontFamily="sans-serif">Without Router</text>
                <text x="728" y="240" fill="#34A47C" fontSize="10" fontFamily="sans-serif" fontWeight="600">With Router (−85%)</text>

                {/* Savings callout */}
                <rect x="535" y="168" width="120" height="34" rx="7" fill="#34A47C" fillOpacity="0.15" stroke="#34A47C" strokeOpacity="0.3" />
                <text x="545" y="183" fill="#34A47C" fontSize="9" fontFamily="sans-serif" fontWeight="600">85% Cost Savings</text>
                <text x="545" y="196" fill="#34A47C" fontSize="8.5" fontFamily="sans-serif">Recaptured</text>

                {/* X-axis */}
                <text x="80" y="270" fill="currentColor" fillOpacity="0.4" fontSize="10" fontFamily="sans-serif">Oct 2025</text>
                <text x="270" y="270" fill="currentColor" fillOpacity="0.4" fontSize="10" fontFamily="sans-serif">Jan 2026</text>
                <text x="470" y="270" fill="currentColor" fillOpacity="0.4" fontSize="10" fontFamily="sans-serif">Apr 2026</text>
                <text x="690" y="270" fill="currentColor" fillOpacity="0.4" fontSize="10" fontFamily="sans-serif">Aug 2026</text>
              </svg>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between pt-5 border-t border-border-subtle gap-3 text-xs">
              <span className="text-text-dim">
                * Based on GSM8K, HumanEval, and production traffic evaluations.
              </span>
              <button
                onClick={() => onNavigate('benchmarks')}
                className="flex items-center gap-1.5 text-accent-primary hover:underline font-medium cursor-pointer"
              >
                Read the benchmark data <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Three Pillars ─── */}
      <section className="max-w-5xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Get more out of your AI stack
          </h2>
          <p className="text-sm text-text-muted">
            Practical guides for deploying intelligent routing, one step at a time.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[
            {
              icon: FileText,
              title: 'Start with the basics',
              desc: '"Where do I even start?" Learn how Model Router classifies incoming requests using lightweight heuristic analyzers without latency overhead.',
              link: 'Explore documentation',
              target: 'docs',
              color: 'accent-primary'
            },
            {
              icon: Code2,
              title: 'Zero-code drop-in proxy',
              desc: '"I have existing OpenAI code." Simply update your base_url to Model Router. It speaks native /v1/chat/completions out of the box.',
              link: 'View quick start',
              target: 'start',
              color: 'accent-purple'
            },
            {
              icon: Layers,
              title: 'Adaptive Thompson Sampling',
              desc: '"I want dynamic learning." The multi-armed bandit continuously adjusts routing weights based on provider latencies and quality.',
              link: 'Configure policies',
              target: 'rules',
              color: 'accent-success'
            }
          ].map((pillar) => {
            const Icon = pillar.icon;
            return (
              <div
                key={pillar.title}
                className="rounded-2xl bg-bg-card border border-border-subtle p-6 flex flex-col justify-between hover:border-accent-primary/50 transition-colors space-y-5"
              >
                <div className="space-y-3">
                  <Icon className={`w-5 h-5 text-${pillar.color}`} />
                  <h3 className="text-[15px] font-semibold text-text-primary">{pillar.title}</h3>
                  <p className="text-[13px] text-text-muted leading-relaxed">{pillar.desc}</p>
                </div>
                <button
                  onClick={() => onNavigate(pillar.target)}
                  className={`text-[13px] font-medium text-${pillar.color} hover:underline flex items-center gap-1.5 cursor-pointer`}
                >
                  {pillar.link} <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>

        <div className="text-center pt-2">
          <button
            onClick={() => onNavigate('start')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent-primary text-white text-[13px] font-semibold hover:brightness-110 shadow-sm cursor-pointer transition-all"
          >
            Get started with Model Router <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

    </div>
  );
};
