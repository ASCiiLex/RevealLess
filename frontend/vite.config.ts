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
        login: 'src/login.tsx',
        register: 'src/register.tsx',
        profile: 'src/profile.tsx',
        edit_profile: 'src/edit_profile.tsx',
        saved_posts: 'src/saved_posts.tsx',
        notifications: 'src/notifications.tsx',
        inbox: 'src/inbox.tsx',
        chat: 'src/chat.tsx',
        follow_list: 'src/follow_list.tsx',
        publicar: 'src/publicar.tsx',
        post_detail: 'src/post_detail.tsx',
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