import React from 'react';
import {
  LayoutDashboard,
  Cpu,
  Binary,
  BrainCircuit,
  LineChart,
  Eye,
  History,
  BookOpen,
  X,
} from 'lucide-react';

export type NavTab =
  | 'overview'
  | 'simulator'
  | 'estimation'
  | 'training'
  | 'comparison'
  | 'visualization'
  | 'history'
  | 'about';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

interface NavItem {
  id: NavTab;
  label: string;
  icon: React.ElementType;
  tag?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview Dashboard', icon: LayoutDashboard },
    { id: 'simulator', label: 'MIMO-OFDM Simulator', icon: Binary },
    { id: 'estimation', label: 'Channel Estimation Lab', icon: Cpu },
    { id: 'training', label: 'ML Model Training', icon: BrainCircuit, tag: 'PyTorch' },
    { id: 'comparison', label: 'Performance Comparison', icon: LineChart },
    { id: 'visualization', label: 'Signal Visualization', icon: Eye },
    { id: 'history', label: 'Experiment History', icon: History },
    { id: 'about', label: 'About & Methodology', icon: BookOpen },
  ];

  const handleItemClick = (tab: NavTab) => {
    onSelectTab(tab);
    if (onCloseMobile) onCloseMobile();
  };

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between p-4 bg-page/95 border-r border-slate-800/80 w-64">
      <div className="space-y-6">
        <div className="flex items-center justify-between md:hidden pb-2 border-b border-slate-800">
          <span className="text-xs font-bold text-white tracking-wider uppercase">Navigation</span>
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="p-1 rounded-lg text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        <div>
          <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Research Modules
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleItemClick(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-cyan-500/10 text-cyan-400 border border-transparent border-l-[3px] border-l-cyan-500'
                      : 'text-slate-400 border border-transparent hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span className="text-left">{item.label}</span>
                  </div>
                  {item.tag && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 text-purple-400 font-mono">
                      {item.tag}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="glass-panel p-3 border-slate-800/60 bg-slate-900/50 text-xs text-slate-400">
        <div className="flex items-center justify-between font-mono text-[11px] text-slate-300 mb-1">
          <span>PIPELINE</span>
          <span className="text-emerald-400 font-semibold">ONLINE</span>
        </div>
        <p className="text-[11px] leading-relaxed">
          MIMO 2x2 | 64-FFT | Comb-Pilots | Rayleigh Fading | LS, MMSE, DNN
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop static sidebar */}
      <aside className="hidden md:flex shrink-0 h-full">{sidebarContent}</aside>

      {/* Mobile drawer with backdrop */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onCloseMobile} />
          <div className="relative z-10 h-full">{sidebarContent}</div>
        </div>
      )}
    </>
  );
};
