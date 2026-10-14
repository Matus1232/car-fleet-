import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // V Dockeri na Windows sa zmeny súborov do kontajnera "nenahlásia", preto ich tam
    // Vite musí sám pravidelne kontrolovať. docker-compose.override.yml nastaví VITE_USE_POLLING.
    watch: { usePolling: process.env.VITE_USE_POLLING === 'true' },
  },
})
