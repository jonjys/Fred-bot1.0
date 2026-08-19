/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0A0A0B",
        card: "#111114",
        border: "#222226",
        live: "#3DFF8A",
        profit: "#3DFF8A",
        loss: "#FF5C5C",
        warn: "#FFB800",
        muted: "#9aa4b2",
      },
      boxShadow: {
        "glow-live": "0 0 8px 1px rgba(61, 255, 138, 0.55)",
        "glow-loss": "0 0 8px 1px rgba(255, 92, 92, 0.45)",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { opacity: 1, boxShadow: "0 0 6px 1px rgba(61,255,138,0.5)" },
          "50%": { opacity: 0.85, boxShadow: "0 0 14px 4px rgba(61,255,138,0.75)" },
        },
      },
      animation: {
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
