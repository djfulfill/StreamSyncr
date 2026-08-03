import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3030,
    proxy: {
      '/api/wetrakr': {
        target: 'https://wetrakr.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/wetrakr/, ''),
      },
      '/api/trakt': {
        target: 'https://api.trakt.tv',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/trakt/, ''),
      },
      '/api/tmdb': {
        target: 'https://api.themoviedb.org',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/tmdb/, ''),
      },
    },
  },
})
