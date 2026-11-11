import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // TOBI clear palette — white/slate/electric blue
        Tobi: {
          // Backgrounds
          bg:           "#ffffff",
          surface:      "#f8fafc",
          "surface-alt":"#f1f5f9",
          border:       "#e2e8f0",

          // Text
          text:         "#0f172a",
          "text-sub":   "#334155",
          "text-dim":   "#475569",
          "text-muted": "#64748b",

          // Accents
          cyan:         "#0284c7",
          "cyan-dim":   "#0369a1",
          "cyan-bright":"#0ea5e9",
          gold:         "#0284c7",
          "gold-dim":   "#0369a1",

          // State
          success:      "#15803d",
          warning:      "#d97706",
          error:        "#b91c1c",

          // Legacy aliases
          blue:         "#0369a1",
          "blue-dark":  "#0f172a",
          glow:         "#0ea5e9",
          panel:        "rgba(255, 255, 255, 0.96)",
          "panel-border":"rgba(15, 23, 42, 0.10)",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      fontSize: {
        "2xs": ["10px", { lineHeight: "14px" }],
        "3xs": ["9px",  { lineHeight: "12px" }],
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "22px",
      },
      animation: {
        "pulse-glow": "pulseGlow 3s ease-in-out infinite",
        "spin-slow":  "spin 8s linear infinite",
        "fade-in":    "fadeInUp 0.25s cubic-bezier(0.16,1,0.3,1) forwards",
        "scale-in":   "scaleFadeIn 0.3s cubic-bezier(0.34,1.56,0.64,1) forwards",
        "breathe":    "breatheGold 2.5s ease-in-out infinite",
        "shimmer":    "shimmer 2s ease-in-out infinite",
        "float":      "subtleFloat 4s ease-in-out infinite",
      },
      keyframes: {
        pulseGlow: {
          "0%,100%": { opacity: "0.6", transform: "scale(1)" },
          "50%":     { opacity: "1",   transform: "scale(1.02)" },
        },
        fadeInUp: {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleFadeIn: {
          "0%":   { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        breatheGold: {
          "0%,100%": { boxShadow: "0 0 12px rgba(212,168,67,0.15), 0 0 4px rgba(212,168,67,0.08)" },
          "50%":     { boxShadow: "0 0 24px rgba(212,168,67,0.30), 0 0 8px rgba(212,168,67,0.15)" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition:  "200% 0" },
        },
        subtleFloat: {
          "0%,100%": { transform: "translateY(0)" },
          "50%":     { transform: "translateY(-3px)" },
        },
      },
      backdropBlur: {
        xs:    "2px",
        "2xl": "24px",
        "3xl": "32px",
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16,1,0.3,1)",
        "spring":   "cubic-bezier(0.34,1.56,0.64,1)",
      },
    },
  },
  plugins: [],
};

export default config;
