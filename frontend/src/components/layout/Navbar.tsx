import React from 'react';
import { Radio, Cpu, RefreshCw, CheckCircle2, AlertCircle, Menu, Sun, Moon } from 'lucide-react';
import { Badge } from '../common/Badge';
import type { HealthResponse } from '../../types';
import type { Theme } from '../../App';

interface NavbarProps {
  health: HealthResponse | null;
  loading: boolean;
  onRefresh: () => void;
  onToggleSidebar?: () => void;
  theme: Theme;
  onToggleTheme: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  loading,
  onRefresh,
  onToggleSidebar,
  theme,
  onToggleTheme,
}) => {
  return (
    <header className="h-16 border-b border-slate-800/80 bg-panel/80 backdrop-blur-md shadow-sm px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-lg bg-slate-800/60 hover:bg-slate-700 text-slate-300 md:hidden transition-colors"
            title="Toggle navigation"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-950/50 shrink-0">
          <Radio className="w-5 h-5 text-white animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base sm:text-lg font-bold tracking-tight bg-gradient-to-r from-cyan-500 to-purple-500 bg-clip-text text-transparent">
              NeuroMIMO
            </h1>
            <Badge variant="cyan" className="font-mono text-[10px]">
              v1.0-RESEARCH
            </Badge>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            AI-Enhanced MIMO-OFDM Channel Estimation & Adaptive Signal Recovery
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {health ? (
          <div className="flex items-center gap-2">
            <Badge variant="green" dot>
              <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" />
              API Connected
            </Badge>
            <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs font-mono text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span>
                PyTorch {health.torch_version} ({health.device.toUpperCase()})
              </span>
            </div>
          </div>
        ) : (
          <Badge variant="rose" dot>
            <AlertCircle className="w-3.5 h-3.5 inline mr-1" />
            Backend Offline
          </Badge>
        )}

        <button
          onClick={onToggleTheme}
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-fg transition-colors"
          title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-fg transition-colors"
          title="Refresh backend status"
        >
          <RefreshCw
            className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`}
          />
        </button>
      </div>
    </header>
  );
};
