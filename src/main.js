import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@fontsource/mukta/latin-400.css'
import '@fontsource/mukta/latin-500.css'
import '@fontsource/mukta/latin-600.css'
import '@fontsource/mukta/latin-700.css'
import './styles/main.css'
import App from './App.vue'
import router from './router'
import { whenSignedOut } from './services/api'
import { useAuthStore } from './stores/auth'

const app = createApp(App).use(createPinia()).use(router)

// The server rejected the session (expired, or the account was deactivated).
whenSignedOut(() => {
  useAuthStore().logout()
  router.replace({ path: '/login' })
})

app.mount('#app')
