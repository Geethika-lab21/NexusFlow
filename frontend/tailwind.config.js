/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
        },
        ink: {
          900: '#17203d',
          700: '#394665',
          500: '#687391',
        },
        lavender: {
          50: '#f8f8ff',
          100: '#f0f1ff',
          200: '#e4e6fb',
        }
      }
    },
  },
  plugins: [],
}
