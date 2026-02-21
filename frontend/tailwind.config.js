/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
    theme: {
        extend: {
            colors: {
                youtube: '#FF0000',
                'youtube-dark': '#282828',
            },
        },
    },
    plugins: [],
};
