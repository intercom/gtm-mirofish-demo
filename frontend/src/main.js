import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useServiceWorker } from './composables/useServiceWorker'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

if (import.meta.env.PROD) {
  const { register } = useServiceWorker()
  register()
}
