import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { perfMonitor } from './lib/perfMonitor'
import './style.css'

perfMonitor.trackRouteNavigation(router)

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

window.addEventListener('load', () => perfMonitor.recordPageLoad())
