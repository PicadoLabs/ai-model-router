/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#07090C",
          secondary: "#101419",
          card: "#14191F",
          cardHover: "#192027",
        },
        border: {
          subtle: "#242B33",
          active: "#3A4552",
        },
        text: {
          primary: "#F5F7FA",
          muted: "#7D8792",
          dim: "#4A525C",
        },
        accent: {
          primary: "#4DA3FF",
          secondary: "#FFB84D",
          success: "#4ADE80",
          error: "#FF6262",
          purple: "#A78BFA",
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
