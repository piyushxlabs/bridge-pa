import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/session': 'http://localhost:8000',
      '/workflow': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
    },
  },
})
