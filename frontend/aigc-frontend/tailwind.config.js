/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./*.tsx",
    "./*.ts",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'Helvetica Neue', 'sans-serif'],
      },
      colors: {
        apple: {
          blue: '#007AFF',
          gray: '#1D1D1F',
          secondary: '#86868B',
          bg: '#F5F5F7',
          border: '#E5E5E7'
        }
      },
      animation: {
        'apple-fade': 'appleFade 0.4s ease-out forwards',
        'apple-slide': 'appleSlide 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        appleFade: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        appleSlide: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } }
      }
    }
  },
  plugins: [],
}
