/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0a0b",
          900: "#111113",
          800: "#1c1c1f",
          700: "#2a2a2e",
        },
        sand: {
          50: "#faf8f5",
          100: "#f3efe8",
          200: "#e6ddd0",
        },
        accent: {
          DEFAULT: "#c8a96b",
          dim: "#a68b52",
          glow: "#e4c98a",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Noto Sans Thai",
          "sans-serif",
        ],
        display: ["ui-sans-serif", "system-ui", "sans-serif"],
      },
      maxWidth: {
        phone: "28rem",
        content: "42rem",
      },
      boxShadow: {
        card: "0 8px 30px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};
