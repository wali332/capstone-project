/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-base': '#0A0F18',
        'brand-surface': '#0F172A',
        'brand-border': '#1E293B',
        'brand-accent': '#22D3EE',
        'brand-mint': '#34D399',
        'brand-danger': '#FB7185',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"IBM Plex Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

