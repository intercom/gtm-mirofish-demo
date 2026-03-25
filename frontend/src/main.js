import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import errorTracker from './lib/errorTracker.js'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
errorTracker.install(app, { router })
app.mount('#app')
