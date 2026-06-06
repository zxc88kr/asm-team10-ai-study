import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/asm-team10-ai-study/',
  server: {
    // WSL2에서 /mnt/e(Windows 드라이브)는 inotify 미지원 → 폴링으로 변경 감지해 HMR 자동 반영.
    watch: { usePolling: true, interval: 300 },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js'],
    globals: true,
  },
})
