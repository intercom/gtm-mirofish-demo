import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useServiceWorker } from './composables/useServiceWorker'
import i18n from './i18n'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')

if (import.meta.env.PROD) {
  const { register } = useServiceWorker()
  register()
}
