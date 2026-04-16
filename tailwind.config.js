/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-base': '#0D0D0F',
        'brand-surface': '#141417',
        'brand-border': '#2A2A30',
        'brand-violet': '#6C63FF',
        'brand-mint': '#00E5A0',
        'brand-danger': '#FF4D6D',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"IBM Plex Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

