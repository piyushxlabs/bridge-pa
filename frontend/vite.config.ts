import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/session': 'http://65.20.89.119:8000',
      '/workflow': 'http://65.20.89.119:8000',
      '/admin': 'http://65.20.89.119:8000',
    },
  },
})
