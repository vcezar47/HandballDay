import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// The backend port comes from backend/.env so both sides stay in sync.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '../backend', '')
  const backendPort = env.PORT || 3000

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': `http://localhost:${backendPort}`,
      },
    },
  }
})
