import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'build' ? '/static/frontend/dist/' : '/',
  build: {
    manifest: true,
    outDir: '../static/frontend/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'src/main.tsx',
        progreso: 'src/progreso.tsx',
        suscripciones: 'src/suscripciones.tsx',
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    cors: true,
    origin: 'http://localhost:5173',
  },
}))