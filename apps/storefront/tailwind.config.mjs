/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#0a0a0b", 900: "#111113", 800: "#1c1c1f", 700: "#2a2a2e", 500: "#6b6b73" },
        sand: { 50: "#faf8f5", 100: "#f3efe8", 200: "#e6ddd0" },
        accent: { DEFAULT: "#c8a96b", dim: "#a68b52", glow: "#e4c98a" },
      },
      maxWidth: {
        site: "72rem",
        phone: "28rem",
      },
    },
  },
  plugins: [],
};
