/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1C2333",
        paper: "#F7F5F0",
        slate: "#4A5568",
        signal: "#2B4C7E",
        signalDark: "#1F3A61",
        amber: "#B8860B",
        amberBg: "#FBF1DC",
        approved: "#2F6B4F",
        approvedBg: "#E7F1EC",
        rust: "#A33B2E",
        rustBg: "#F6E9E7",
        hairline: "#D8D4CA",
      },
      fontFamily: {
        serif: ["'Source Serif 4'", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
