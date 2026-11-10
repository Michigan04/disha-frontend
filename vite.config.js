import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// base './' lets the built app run from any folder or static host.
// The /api proxy routes dev-server requests to the FastAPI backend so
// the frontend can call /api/... without CORS issues locally.
export default defineConfig({
  plugins: [vue()],
  base: './',
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
