import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Policy of the single-page app. Must equal SPA_CSP in backend/app/security/headers.py (a backend test
// checks this) and is what Apache sends in production. `vite preview` serves the built app with it, so
// `npm run build && npm run preview` shows exactly what the CSP allows. The dev server does not send it:
// Vite's hot reload needs inline scripts.
const SPA_CSP =
  "default-src 'self'; script-src 'self' https://challenges.cloudflare.com; " +
  "style-src 'self'; style-src-attr 'unsafe-inline'; img-src 'self' data: blob:; " +
  "connect-src 'self'; frame-src https://challenges.cloudflare.com; " +
  "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"

// The backend port comes from backend/.env so both sides stay in sync.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '../backend', '')
  const backendPort = env.PORT || 3000
  // sitemap.xml and robots.txt are built from the database, so the backend serves them
  const proxy = {
    '/api': `http://localhost:${backendPort}`,
    '/sitemap.xml': `http://localhost:${backendPort}`,
    '/robots.txt': `http://localhost:${backendPort}`,
  }

  return {
    plugins: [react()],
    server: { port: 5173, proxy },
    preview: {
      port: 4173,
      proxy,
      headers: {
        'Content-Security-Policy': SPA_CSP,
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
      },
    },
  }
})
