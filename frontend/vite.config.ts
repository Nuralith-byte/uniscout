import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // локально фронт ходит в FastAPI без CORS-возни; в проде задай VITE_API_URL
      '/api': 'http://localhost:8000',
    },
  },
})
