import React, { useState, useRef, useEffect } from 'react';
import { 
  Activity, 
  Compass, 
  Layers, 
  Cpu, 
  BarChart3, 
  Sliders, 
  Radio,
  Trophy,
  Sun,
  Moon,
  BookOpen,
  Sparkles,
  ChevronDown,
  Menu,
  Zap
} from 'lucide-react';
import { useTheme } from '../ThemeContext';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onlineStatus?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const { theme, toggleTheme } = useTheme();
  const [sectionsOpen, setSectionsOpen] = useState<boolean>(false);
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setSectionsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const sectionItems = [
    { id: 'traffic', label: 'Live Traffic', icon: Radio },
    { id: 'models', label: 'Model Catalog', icon: Cpu },
    { id: 'rules', label: 'Routing Rules', icon: Layers },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Sliders },
  ];

  const isSectionActive = sectionItems.some(s => s.id === activeTab);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border-subtle bg-bg-primary/95 backdrop-blur-md">
      <div className="max-w-[1200px] mx-auto px-5 sm:px-8 h-14 flex items-center justify-between gap-6">
        
        {/* Brand */}
        <button 
          onClick={() => setActiveTab('overview')}
          className="flex items-center gap-2.5 cursor-pointer select-none shrink-0 group"
        >
          <div className="w-8 h-8 rounded-lg bg-bg-secondary border border-border-subtle flex items-center justify-center overflow-hidden p-0.5">
            <img 
              src="/logo.png" 
              alt="Model Router" 
              className="w-full h-full object-contain" 
            />
          </div>
          <span className="font-sans font-bold text-[15px] text-text-primary tracking-tight">
            Model Router
          </span>
        </button>

        {/* Center Nav */}
        <nav className="hidden md:flex items-center gap-1">
          
          {/* Sections Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setSectionsOpen(!sectionsOpen)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors cursor-pointer ${
                isSectionActive || sectionsOpen
                  ? 'text-text-primary'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              <Menu className="w-4 h-4" />
              <span>Sections</span>
            </button>

            {sectionsOpen && (
              <div className="absolute left-0 top-full mt-2 w-56 rounded-xl bg-bg-card border border-border-subtle p-1.5 shadow-xl z-50 space-y-0.5">
                {sectionItems.map((sec) => {
                  const SecIcon = sec.icon;
                  const isActive = activeTab === sec.id;
                  return (
                    <button
                      key={sec.id}
                      onClick={() => { setActiveTab(sec.id); setSectionsOpen(false); }}
                      className={`w-full text-left px-3 py-2 rounded-lg text-[13px] font-medium transition-colors flex items-center gap-2.5 cursor-pointer ${
                        isActive
                          ? 'bg-accent-primary/10 text-accent-primary'
                          : 'text-text-muted hover:text-text-primary hover:bg-bg-secondary'
                      }`}
                    >
                      <SecIcon className="w-4 h-4" />
                      <span>{sec.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Primary links */}
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'dashboard', label: 'Control Room' },
            { id: 'playground', label: 'Playground' },
            { id: 'benchmarks', label: 'Benchmarks' },
            { id: 'docs', label: 'Docs' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-3 py-1.5 rounded-lg text-[13px] font-medium transition-colors cursor-pointer ${
                activeTab === item.id
                  ? 'text-text-primary font-semibold'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* Right Controls */}
        <div className="flex items-center gap-2 shrink-0">
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-lg text-text-muted hover:text-text-primary transition-colors cursor-pointer"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-[18px] h-[18px]" /> : <Moon className="w-[18px] h-[18px]" />}
          </button>

          <button
            onClick={() => setActiveTab('start')}
            className="px-4 py-1.5 rounded-lg bg-accent-primary text-white text-[13px] font-semibold hover:brightness-110 transition-all cursor-pointer"
          >
            Get started
          </button>
        </div>

      </div>

      {/* Mobile Nav */}
      <div className="md:hidden border-t border-border-subtle bg-bg-secondary/50 px-4 py-2 overflow-x-auto flex items-center gap-1 no-scrollbar">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'dashboard', label: 'Control Room' },
          { id: 'playground', label: 'Playground' },
          { id: 'benchmarks', label: 'Benchmarks' },
          { id: 'docs', label: 'Docs' },
          ...sectionItems,
        ].map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap shrink-0 transition-colors cursor-pointer ${
                isActive
                  ? 'bg-accent-primary text-white font-semibold'
                  : 'text-text-muted hover:text-text-primary bg-bg-card border border-border-subtle'
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
};
