import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// base './' lets the built app run from any folder or static host
export default defineConfig({
  plugins: [vue()],
  base: './',
})
