import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

import LandingView from './views/LandingView.vue'
import ScenarioBuilderView from './views/ScenarioBuilderView.vue'
import GraphView from './views/GraphView.vue'
import SimulationView from './views/SimulationView.vue'
import ReportView from './views/ReportView.vue'
import ChatView from './views/ChatView.vue'
import SettingsView from './views/SettingsView.vue'
import LoginView from './views/LoginView.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  { path: '/scenarios/:id', name: 'scenario-builder', component: ScenarioBuilderView, props: true },
  { path: '/graph/:taskId', name: 'graph', component: GraphView, props: true },
  { path: '/simulation/:taskId', name: 'simulation', component: SimulationView, props: true },
  { path: '/report/:taskId', name: 'report', component: ReportView, props: true },
  { path: '/chat/:taskId', name: 'chat', component: ChatView, props: true },
  { path: '/settings', name: 'settings', component: SettingsView },
  { path: '/login', name: 'login', component: LoginView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
