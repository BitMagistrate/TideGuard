import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand palette: deep teal, ocean blue, sand
        teal: {
          500: "#0F766E",
          600: "#0d6660",
          700: "#0b5550",
        },
        ocean: {
          500: "#0369A1",
          600: "#025980",
        },
        sand: {
          50: "#FEF8E7",
          100: "#FEF3C7",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto"],
      },
    },
  },
  plugins: [],
};

export default config;
