import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base solo aplica al build de producción (para que WhiteNoise sirva los
// assets desde /static/frontend/dist/). En dev, Vite sirve desde su raíz
// normal; Django carga los módulos directamente por URL absoluta al
// servidor de Vite (ver core/templatetags/vite_tags.py), sin visitar
// nunca localhost:5173 en el navegador.
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