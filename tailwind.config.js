/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'lime-cream': '#f7fce8',
        'lime-cream-dark': '#eef7d3',
        'canary': '#fde047',
        'canary-dark': '#facc15',
        'ink': '#0f172a',
        'ink-light': '#334155',
      },
      fontFamily: {
        sans: ['Outfit', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};