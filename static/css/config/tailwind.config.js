/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../../templates/**/*.html",
    "../../app/templates/**/*.html",
    "../../static/js/**/*.js",
    "../../app/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--primary-color)',
          dark: 'var(--primary-hover)'
        },
        gray: {
          100: 'var(--gray-100)',
          200: 'var(--gray-200)',
          300: 'var(--gray-300)',
          400: 'var(--gray-400)',
          500: 'var(--gray-500)',
          600: 'var(--gray-600)',
        },
        blue: {
          500: 'var(--blue-500)',
          600: 'var(--blue-600)',
          700: 'var(--blue-700)',
        },
        red: {
          500: 'var(--red-500)'
        },
        green: {
          500: 'var(--green-500)'
        },
        yellow: {
          500: 'var(--yellow-500)'
        },
        secondary: 'var(--text-secondary)',
        'text-color': 'var(--text-color)',
        'text-secondary': 'var(--text-secondary)',
        'text-brand': 'var(--text-brand)',
        'border-color': 'var(--border-color)',
        'background-default': 'var(--background-default)',
        'background-neutral': 'var(--background-neutral)',
        'background-brand': 'var(--background-brand)',
        'background-light': 'var(--background-light)',
        'background-placeholder': 'var(--background-placeholder)',
      },
      fontFamily: {
        sans: ['Roboto', 'Inter', 'sans-serif'],
      },
      spacing: {
        'xs': 'var(--spacing-xs)',
        'sm': 'var(--spacing-sm)',
        'md': 'var(--spacing-md)',
        'lg': 'var(--spacing-lg)',
        'xl': 'var(--spacing-xl)',
        '2xl': 'var(--spacing-2xl)',
      },
      borderRadius: {
        'sm': 'var(--border-radius-sm)',
        'md': 'var(--border-radius-md)',
        'lg': 'var(--border-radius-lg)',
      },
      boxShadow: {
        'sm': 'var(--shadow-sm)',
        'DEFAULT': 'var(--shadow)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
      }
    },
  },
  plugins: [],
}
