import React, { useEffect, useRef, useState } from 'react';
import { Palette, Check } from 'lucide-react';
import { COLOR_THEMES } from '../../theme';
import type { ColorTheme } from '../../theme';

interface ThemePickerProps {
  theme: ColorTheme;
  onChangeTheme: (theme: ColorTheme) => void;
}

export const ThemePicker: React.FC<ThemePickerProps> = ({ theme, onChangeTheme }) => {
  const [open, setOpen] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close the menu on an outside click or the Escape key
  useEffect(() => {
    if (!open) return;
    const handleClick = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className={`p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 border text-slate-300 hover:text-white transition-colors ${
          open ? 'border-cyan-500/60 text-cyan-400' : 'border-slate-700'
        }`}
        title="Change colour theme"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <Palette className="w-4 h-4" />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-60 rounded-xl bg-panel border border-slate-700 shadow-2xl p-1.5 z-50"
        >
          <p className="px-2.5 pt-1.5 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Colour Theme
          </p>
          {COLOR_THEMES.map((option) => {
            const active = option.id === theme;
            return (
              <button
                key={option.id}
                role="menuitemradio"
                aria-checked={active}
                onClick={() => {
                  onChangeTheme(option.id);
                  setOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-2.5 py-2 rounded-lg text-left transition-colors ${
                  active ? 'bg-cyan-500/10 border border-cyan-500/30' : 'border border-transparent hover:bg-slate-800/70'
                }`}
              >
                <span className="flex -space-x-1.5 shrink-0">
                  {option.swatch.map((color) => (
                    <span
                      key={color}
                      className="w-4 h-4 rounded-full border-2 border-slate-900"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </span>
                <span className="flex-1 min-w-0">
                  <span className={`block text-sm font-medium ${active ? 'text-cyan-400' : 'text-slate-200'}`}>
                    {option.label}
                  </span>
                  <span className="block text-[11px] text-slate-400">{option.description}</span>
                </span>
                {active && <Check className="w-4 h-4 text-cyan-400 shrink-0" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
