/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        wine: {
          50: '#fdf2f4',
          100: '#fce7eb',
          200: '#f9d0da',
          300: '#f4a9bc',
          400: '#ed7795',
          500: '#e14a72',
          600: '#722f37', // Primary wine color (burgundy)
          700: '#5c252c',
          800: '#4d2027',
          900: '#421d23',
          950: '#260c0f',
        },
      },
      animation: {
        'bounce': 'bounce 1s infinite',
      },
    },
  },
  plugins: [],
}
