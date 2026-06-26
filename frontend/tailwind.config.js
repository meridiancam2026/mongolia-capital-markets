/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        sage: {
          bg:           '#e6ede1',
          sidebar:      '#eef2ea',
          surface:      '#f4f7f1',
          card:         '#ffffff',
          text:         '#1f2a18',
          muted:        '#5d6a52',
          faint:        '#8a977c',
          border:       '#d3dcc6',
          'card-border':'#cbd6bb',
          divider:      '#e2e8da',
          row:          '#edf1e7',
          hover:        '#f1f5ec',
          up:           '#2f8f4e',
          down:         '#c4453b',
          accent:       '#2b6cb0',
          amber:        '#b07d18',
        },
      },
      fontFamily: {
        mono:  ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        tight: ['"Inter Tight"', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
