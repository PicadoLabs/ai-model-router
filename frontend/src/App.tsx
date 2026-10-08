import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Overview } from './pages/Overview';
import { Dashboard } from './pages/Dashboard';
import { Playground } from './pages/Playground';
import { Traffic } from './pages/Traffic';
import { Models } from './pages/Models';
import { Rules } from './pages/Rules';
import { Analytics } from './pages/Analytics';
import { BenchmarksPage } from './pages/BenchmarksPage';
import { SettingsPage } from './pages/SettingsPage';
import { DocsPage } from './pages/DocsPage';
import { StartPage } from './pages/StartPage';
import { MessageSquarePlus, GitBranch, Sparkles, Code2 } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex flex-col selection:bg-accent-primary/20 relative">
      {/* Top AI Control Room Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {activeTab === 'overview' && <Overview onNavigate={setActiveTab} />}
        {activeTab === 'docs' && <DocsPage onNavigate={setActiveTab} />}
        {activeTab === 'start' && <StartPage onNavigate={setActiveTab} />}
        {activeTab === 'dashboard' && <Dashboard onNavigate={setActiveTab} />}
        {activeTab === 'playground' && <Playground />}
        {activeTab === 'benchmarks' && <BenchmarksPage />}
        {activeTab === 'traffic' && <Traffic />}
        {activeTab === 'models' && <Models />}
        {activeTab === 'rules' && <Rules />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>

      {/* Footer */}
      <footer className="border-t border-border-subtle py-8 mt-16">
        <div className="max-w-[1200px] mx-auto px-5 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[13px] text-text-muted">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-md bg-bg-secondary border border-border-subtle flex items-center justify-center p-0.5">
              <img src="/logo.png" alt="MR" className="w-full h-full object-contain" />
            </div>
            <span className="font-semibold text-text-primary">Model Router</span>
          </div>

          <div className="flex items-center gap-4 text-text-dim text-[12px]">
            <button onClick={() => setActiveTab('docs')} className="hover:text-text-primary cursor-pointer">
              Documentation
            </button>
            <button onClick={() => setActiveTab('start')} className="hover:text-text-primary cursor-pointer">
              Get Started
            </button>
            <a 
              href="https://github.com/PicadoLabs/ai-model-router" 
              target="_blank" 
              rel="noreferrer" 
              className="hover:text-text-primary"
            >
              GitHub
            </a>
            <span>Apache 2.0</span>
          </div>
        </div>
      </footer>

      {/* Floating Feedback */}
      <div className="fixed bottom-4 right-4 z-40">
        <a
          href="https://github.com/PicadoLabs/ai-model-router/issues/new"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-card border border-border-subtle hover:border-accent-primary text-[12px] text-text-muted hover:text-text-primary shadow-lg transition-colors"
        >
          <MessageSquarePlus className="w-3.5 h-3.5 text-accent-primary" />
          <span>Comment / Suggest a change</span>
        </a>
      </div>
    </div>
  );
}

export default App;
