import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          yellow: '#FFD826',
          dark: '#101010',
          gray: '#8A8A8A',
          white: '#FFFFFF',
          lightGray: '#F5F5F5',
        },
      },
    },
  },
  plugins: [],
};

export default config;
