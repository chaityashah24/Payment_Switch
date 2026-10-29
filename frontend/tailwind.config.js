/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./frontend/index.html",
    "./frontend/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#0a192f",
          dark: "#0f172a",
          teal: "#0d9488",
          tealLight: "#14b8a6",
          slate: "#334155",
          surface: "#f8fafc",
          border: "#e2e8f0",
        }
      }
    },
  },
  plugins: [],
}
