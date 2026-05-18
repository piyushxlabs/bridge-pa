import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/session': 'https://bridge-pa-production.up.railway.app',
      '/workflow': 'https://bridge-pa-production.up.railway.app',
      '/admin': 'https://bridge-pa-production.up.railway.app',
    },
  },
})
