import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        "background-secondary": "var(--background-secondary)",
        section: "var(--section-background)",
        card: "var(--card)",
        navbar: "var(--navbar)",
        footer: "var(--footer)",
        "hover-bg": "var(--hover-bg)",
        foreground: "var(--foreground)",
        "foreground-secondary": "var(--foreground-secondary)",
        primary: {
          DEFAULT: "var(--primary)",
          hover: "var(--primary-hover)",
          secondary: "var(--primary-secondary)",
        },
        "soft-blue": "var(--soft-blue)",
        "soft-lavender": "var(--soft-lavender)",
        "soft-peach": "var(--soft-peach)",
        border: "var(--border)",
        success: "var(--success)",
        warning: "var(--warning)",
        error: "var(--error)",
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "var(--shadow-soft)",
        card: "var(--shadow-card)",
      },
      animation: {
        "fade-in": "fade-in 0.5s ease-out both",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
