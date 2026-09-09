import React from 'react';
import { 
  Activity, 
  Compass, 
  Layers, 
  Cpu, 
  BarChart3, 
  Sliders, 
  Radio,
  Sun,
  Moon
} from 'lucide-react';
import { useTheme } from '../ThemeContext';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onlineStatus?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, onlineStatus = true }) => {
  const { theme, toggleTheme } = useTheme();
  const navItems = [
    { id: 'dashboard', label: 'Control Room', icon: Activity },
    { id: 'playground', label: 'Playground', icon: Compass },
    { id: 'traffic', label: 'Live Traffic', icon: Radio },
    { id: 'models', label: 'Models', icon: Cpu },
    { id: 'rules', label: 'Rules', icon: Layers },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Sliders },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border-subtle bg-bg-primary/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Brand / Logo */}
        <div 
          onClick={() => setActiveTab('dashboard')}
          className="flex items-center gap-3 cursor-pointer select-none shrink-0 group"
        >
          <div className="w-10 h-10 rounded-xl bg-bg-secondary border border-accent-primary/40 flex items-center justify-center overflow-hidden shadow-[0_0_18px_rgba(56,148,255,0.25)] group-hover:border-accent-primary transition-all p-1">
            <img 
              src="/logo.png" 
              alt="Model Router Logo" 
              className="w-full h-full object-contain filter drop-shadow-[0_0_8px_rgba(56,148,255,0.5)]" 
            />
          </div>
          
          <div className="flex flex-col justify-center">
            <div className="flex items-center gap-2 leading-none">
              <span className="font-mono font-extrabold text-sm tracking-wider text-text-primary whitespace-nowrap">
                MODEL ROUTER
              </span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-accent-primary/15 text-accent-primary border border-accent-primary/30 leading-none">
                v1.0
              </span>
            </div>
            <span className="text-[10px] font-mono text-text-muted mt-1 leading-none tracking-tight">
              AI Traffic Control Room
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden lg:flex items-center gap-1.5 p-1 rounded-xl bg-bg-secondary/80 border border-border-subtle/80">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all duration-150 whitespace-nowrap ${
                  isActive
                    ? 'bg-accent-primary text-bg-primary shadow-[0_0_12px_rgba(56,148,255,0.4)] font-bold'
                    : 'text-text-muted hover:text-text-primary hover:bg-bg-card'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-bg-primary stroke-[2.5]' : 'text-text-muted stroke-[2]'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Mobile & Tablet Nav Pill Scroll */}
        <nav className="flex lg:hidden overflow-x-auto items-center gap-1 py-1 no-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono transition-all shrink-0 ${
                  isActive
                    ? 'bg-accent-primary text-bg-primary font-bold'
                    : 'text-text-muted hover:text-text-primary'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Status Indicator */}
        <div className="hidden sm:flex items-center gap-2 shrink-0">
          <button 
            onClick={toggleTheme}
            className="p-1.5 rounded-xl bg-bg-secondary border border-border-subtle text-text-muted hover:text-text-primary hover:border-border-active transition-all"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-bg-secondary border border-border-subtle font-mono text-xs shadow-inner">
            <span className={`w-2 h-2 rounded-full ${onlineStatus ? 'bg-accent-success shadow-[0_0_8px_#10B981]' : 'bg-accent-error'}`} />
            <span className="text-[11px] font-bold tracking-wide text-text-primary whitespace-nowrap">
              ROUTER READY
            </span>
          </div>
        </div>

      </div>
    </header>
  );
};
