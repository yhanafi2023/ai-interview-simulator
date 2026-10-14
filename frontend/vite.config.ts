/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    exclude: ['e2e/**', 'node_modules/**'],
  },
    server: {
    proxy: {
      // Adjust these prefixes to match the paths api.ts actually requests
      '/auth': { target: process.env.VITE_PROXY_TARGET, changeOrigin: true },
      '/sessions': { target: process.env.VITE_PROXY_TARGET, changeOrigin: true },
      '/questions': { target: process.env.VITE_PROXY_TARGET, changeOrigin: true },
      '/jobs': { target: process.env.VITE_PROXY_TARGET, changeOrigin: true },
      '/health': { target: process.env.VITE_PROXY_TARGET, changeOrigin: true },
    },
  },
})
