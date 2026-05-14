import rtlPlugin from 'tailwindcss-rtl'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        sand: {
          50:  '#fbf7f1',
          100: '#f4ead9',
          200: '#e9d4b3',
          300: '#dbb682',
          400: '#cc9656',
          500: '#bd7d3d',
          600: '#a56432',
          700: '#824c2b',
          800: '#5e3722',
          900: '#3e2417',
        },
        terracotta: {
          50:  '#fdf4f0',
          100: '#fae3d8',
          200: '#f3c4ad',
          300: '#e99c79',
          400: '#dc7148',
          500: '#cd5028',
          600: '#b53d1f',
          700: '#8f2e1c',
          800: '#67241a',
          900: '#421810',
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 4px 20px -2px rgb(0 0 0 / 0.06)',
      }
    },
  },
  plugins: [
    // Adds `start-*` / `end-*` logical utilities (e.g. ms-3 / me-3) that
    // mirror automatically when `dir="rtl"` is set on the document.
    rtlPlugin,
  ],
}
