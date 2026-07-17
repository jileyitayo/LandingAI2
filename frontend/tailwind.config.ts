import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "rgb(var(--surface) / <alpha-value>)",
        card: {
          DEFAULT: "rgb(var(--card) / <alpha-value>)",
          muted: "rgb(var(--card-muted) / <alpha-value>)",
        },
        border: "rgb(var(--border) / <alpha-value>)",
        fg: "rgb(var(--fg) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        brand: {
          DEFAULT: "rgb(var(--brand) / <alpha-value>)",
          2: "rgb(var(--brand-2) / <alpha-value>)",
          fg: "rgb(var(--on-brand) / <alpha-value>)",
        },
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(to right, rgb(var(--brand)), rgb(var(--brand-2)))",
        "brand-gradient-br":
          "linear-gradient(to bottom right, rgb(var(--brand)), rgb(var(--brand-2)))",
      },
      boxShadow: {
        "glow-sm": "0 4px 18px -6px rgb(var(--brand-2) / 0.45)",
        glow: "0 8px 30px -6px rgb(var(--brand-2) / 0.55), 0 2px 10px -2px rgb(var(--brand) / 0.35)",
        card: "0 1px 2px rgb(23 19 34 / 0.04), 0 6px 16px -6px rgb(23 19 34 / 0.06)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", ...defaultTheme.fontFamily.sans],
        display: ["var(--font-display)", ...defaultTheme.fontFamily.sans],
      },
      keyframes: {
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        shimmer: "shimmer 2s infinite",
      },
    },
  },
  plugins: [],
};

export default config;
