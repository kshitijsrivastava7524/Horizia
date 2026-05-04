module.exports = {
  content: [
    "../frontend/**/*.{html,js}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'primary': '#ffffff',
        'secondary': '#e5e5e5',
        'text-main': '#1a1a1a',
        'text-subtle': '#6b7280',
        'dark-primary': '#1a1a1a',
        'dark-secondary': '#333333',
        'dark-text-main': '#f0f0f0',
        'dark-text-subtle': '#b0b0b0',
        'accent-blue': '#2874fc',
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
}