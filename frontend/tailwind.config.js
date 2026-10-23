/** @type {import('tailwindcss').Config} */

// Colours come from CSS variables defined in src/index.css so every colour theme
// shares the same class names.
const fromVar = (name) => `rgb(var(--${name}) / <alpha-value>)`;
const SHADES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950];
const themedPalette = (name) =>
  Object.fromEntries(SHADES.map((shade) => [shade, fromVar(`${name}-${shade}`)]));

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: themedPalette('slate'),
        cyan: themedPalette('cyan'),
        purple: themedPalette('purple'),
        emerald: themedPalette('emerald'),
        rose: themedPalette('rose'),
        amber: themedPalette('amber'),
        page: fromVar('page'),
        panel: fromVar('panel'),
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      }
    },
  },
  plugins: [],
}
