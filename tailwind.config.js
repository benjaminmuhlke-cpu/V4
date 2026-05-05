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
        sans: ['"Source Sans 3"', 'Helvetica', 'Arial', 'sans-serif'],
        display: ['"Playfair Display"', 'Georgia', 'serif'],
      },
      colors: {
        'earth-dark': '#1C1208',
        'earth-brown': '#4A3728',
        'warm-brown': '#7C5B3A',
        'earth-tan': '#B08A60',
        'earth-stone': '#C9B49A',
        cream: '#F4EDE0',
        forest: '#2C4A2E',
        moss: '#4E6B3A',
        rust: '#8B3A1E',
        'earth-amber': '#C67B2E',
      },
      letterSpacing: {
        widest: '0.25em',
        'ultra-wide': '0.35em',
      },
      transitionTimingFunction: {
        'ease-out-expo': 'cubic-bezier(0.19, 1, 0.22, 1)',
      },
    },
  },
  plugins: [],
}
