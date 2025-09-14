import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
        },
      },
    },
  },
  server: {
    port: 3080,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8089',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:8089',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8089',
        changeOrigin: true,
      },
      '/.well-known': {
        target: 'http://localhost:8089',
        changeOrigin: true,
      },
    },
  },
})
