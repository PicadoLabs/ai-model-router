import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { Playground } from './pages/Playground';
import { Traffic } from './pages/Traffic';
import { Models } from './pages/Models';
import { Rules } from './pages/Rules';
import { Analytics } from './pages/Analytics';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex flex-col selection:bg-accent-primary/20">
      {/* Top AI Control Room Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {activeTab === 'dashboard' && <Dashboard onNavigate={setActiveTab} />}
        {activeTab === 'playground' && <Playground />}
        {activeTab === 'traffic' && <Traffic />}
        {activeTab === 'models' && <Models />}
        {activeTab === 'rules' && <Rules />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>

      {/* Footer */}
      <footer className="border-t border-border-subtle bg-bg-secondary/80 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs text-text-muted">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-lg bg-[#0D1117] border border-border-subtle flex items-center justify-center p-0.5">
              <img src="/logo.png" alt="MR" className="w-full h-full object-contain" />
            </div>
            <span className="font-bold text-text-primary">Model Router</span>
            <span className="text-text-dim">•</span>
            <span>Intelligent LLM Request Dispatcher</span>
          </div>
          <div className="text-text-dim text-[11px]">
            Local-First • Provider-Agnostic • Open-Source MIT
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
