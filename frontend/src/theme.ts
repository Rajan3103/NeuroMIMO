// Dark colour themes. Each id matches a [data-theme] block in index.css
// (Neon is the default ":root" palette).
export const COLOR_THEMES = [
  { id: 'neon', label: 'Neon', description: 'Cyan & purple (original)', swatch: ['#06b6d4', '#a855f7'] },
  { id: 'nebula', label: 'Nebula', description: 'Violet & magenta', swatch: ['#8b5cf6', '#d946ef'] },
  { id: 'matrix', label: 'Matrix', description: 'Emerald & teal', swatch: ['#10b981', '#14b8a6'] },
  { id: 'solar', label: 'Solar', description: 'Amber & rose', swatch: ['#f59e0b', '#f43f5e'] },
] as const;

export type ColorTheme = (typeof COLOR_THEMES)[number]['id'];

const THEME_STORAGE_KEY = 'neuromimo-theme';
const DEFAULT_THEME: ColorTheme = 'neon';

export function loadSavedTheme(): ColorTheme {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    return COLOR_THEMES.some((t) => t.id === saved) ? (saved as ColorTheme) : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

export function applyTheme(theme: ColorTheme): void {
  // The default theme lives on :root, so it needs no attribute
  if (theme === DEFAULT_THEME) {
    document.documentElement.removeAttribute('data-theme');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage can be unavailable (private mode); the theme still applies for this visit
  }
}
