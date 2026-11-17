import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // V Dockeri na Windows sa zmeny súborov do kontajnera "nenahlásia", preto ich tam
    // Vite musí sám pravidelne kontrolovať. docker-compose.override.yml nastaví VITE_USE_POLLING.
    watch: { usePolling: process.env.VITE_USE_POLLING === 'true' },
    // Požiadavky na /api pošle Vite ďalej na backend a /api z adresy odstráni
    // (/api/vehicles -> http://localhost:8000/vehicles). Prehliadač tak vidí jednu adresu
    // (localhost:5173) a cookie s tokenom funguje rovnako ako v produkcii za nginx.
    // V Dockeri je backend na http://api:8000, nastaví to docker-compose.override.yml.
    proxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
