import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useServiceWorker } from './composables/useServiceWorker'
import i18n from './i18n'
import { perfMonitor } from './lib/perfMonitor'
import errorTracker from './lib/errorTracker.js'
import './style.css'

perfMonitor.trackRouteNavigation(router)

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)
errorTracker.install(app, { router })
app.mount('#app')

if (import.meta.env.PROD) {
  const { register } = useServiceWorker()
  register()
}

window.addEventListener('load', () => perfMonitor.recordPageLoad())
