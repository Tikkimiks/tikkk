/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/*.{html,js}',
    '../main/**/*.{html,js}'
  ],
  theme: {
    extend: {
        backgroundImage: {
            'main-ph' : "url('/security/main/static/main/main-ph.png')"
        }
    },
  },
  plugins: [],
}

