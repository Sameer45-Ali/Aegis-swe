/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090d16",
        surface: "#111827",
        surfaceHover: "#1f2937",
        accent: "#00f0ff",
        accentGlow: "rgba(0, 240, 255, 0.15)",
        nodePass: "#10b981",
        nodeFail: "#ef4444",
        nodePending: "#f59e0b"
      }
    },
  },
  plugins: [],
};