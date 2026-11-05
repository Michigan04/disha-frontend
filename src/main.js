import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@fontsource/mukta/latin-400.css'
import '@fontsource/mukta/latin-500.css'
import '@fontsource/mukta/latin-600.css'
import '@fontsource/mukta/latin-700.css'
import './styles/main.css'
import App from './App.vue'
import router from './router'

createApp(App).use(createPinia()).use(router).mount('#app')
