import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // TOBI warm palette — ivory/cream/brown/gold
        Tobi: {
          // Backgrounds
          bg:           "#faf7f2",
          surface:      "#f5f0e8",
          "surface-alt":"#ede5d8",
          border:       "#e4dace",

          // Text
          text:         "#2e1f14",
          "text-sub":   "#6b5744",
          "text-dim":   "#8c7a6b",
          "text-muted": "#b8ac9e",

          // Accents — gold/amber
          cyan:         "#d4a843",   // "cyan" slot → gold (used widely in existing classes)
          "cyan-dim":   "#b8922e",
          "cyan-bright":"#ddb84e",
          gold:         "#d4a843",
          "gold-dim":   "#9a7a26",

          // State
          success:      "#5a8a5a",
          warning:      "#c97c2a",
          error:        "#b85252",

          // Legacy aliases so existing components don't break
          blue:         "#5a7a9a",
          "blue-dark":  "#1a2a3a",
          glow:         "#d4a843",
          panel:        "rgba(245, 240, 232, 0.92)",
          "panel-border":"rgba(180, 160, 130, 0.20)",
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
