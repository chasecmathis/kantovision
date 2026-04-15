import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-unbounded)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
        body: ["var(--font-dm-sans)", "sans-serif"],
      },
      colors: {
        bg: {
          base: "#080810",
          surface: "#0e0e1a",
          elevated: "#141426",
          border: "#1c1c30",
        },
        accent: {
          DEFAULT: "#6c63ff",
          dim: "#3d3880",
        },
        text: {
          primary: "#e8e6ff",
          secondary: "#8884aa",
          muted: "#4a4870",
        },
        type: {
          normal: "#9CA3AF",
          fire: "#F97316",
          water: "#60A5FA",
          electric: "#FBBF24",
          grass: "#4ADE80",
          ice: "#67E8F9",
          fighting: "#EF4444",
          poison: "#C084FC",
          ground: "#D97706",
          flying: "#818CF8",
          psychic: "#F472B6",
          bug: "#84CC16",
          rock: "#A78BFA",
          ghost: "#7C3AED",
          dragon: "#6366F1",
          dark: "#78716C",
          steel: "#94A3B8",
          fairy: "#F9A8D4",
        },
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(108,99,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(108,99,255,0.04) 1px, transparent 1px)",
        "scanlines":
          "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 4px)",
      },
      backgroundSize: {
        "grid-sm": "20px 20px",
        "grid-md": "40px 40px",
      },
      animation: {
        "fade-up": "fadeUp 0.4s ease forwards",
        "fade-in": "fadeIn 0.3s ease forwards",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "stat-fill": "statFill 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "scan-line": "scanLine 3s linear infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
        statFill: {
          "0%": { width: "0%" },
          "100%": { width: "var(--stat-width)" },
        },
        scanLine: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
