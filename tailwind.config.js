/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"America"', 'Helvetica', 'Arial', 'sans-serif'],
        display: ['"America"', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        stone: {
          50: '#fafaf9',
          100: '#f5f5f4',
          200: '#e7e5e4',
          300: '#d6d3d1',
          400: '#a8a29e',
          500: '#78716c',
          600: '#57534e',
          700: '#44403c',
          800: '#292524',
          900: '#1c1917',
          950: '#0c0a09',
        },
      },
      letterSpacing: {
        widest: '0.25em',
        'ultra-wide': '0.35em',
      },
      transitionTimingFunction: {
        'ease-out-expo': 'cubic-bezier(0.19, 1, 0.22, 1)',
        'ease-in-out-quint': 'cubic-bezier(0.83, 0, 0.17, 1)',
      },
    },
  },
  plugins: [],
}
