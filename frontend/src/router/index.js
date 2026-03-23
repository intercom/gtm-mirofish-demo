import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '../views/LandingView.vue'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingView,
  },
  {
    path: '/scenarios/:id',
    name: 'scenario-builder',
    component: () => import('../views/ScenarioBuilderView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/graph/:taskId',
    name: 'graph',
    component: () => import('../views/GraphView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/simulation/:taskId',
    name: 'simulation',
    component: () => import('../views/SimulationView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/report/:taskId',
    name: 'report',
    component: () => import('../views/ReportView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/chat/:taskId',
    name: 'chat',
    component: () => import('../views/ChatView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
]

let authEnabled = false
let authenticated = false

export function setAuthState({ enabled, loggedIn }) {
  if (enabled !== undefined) authEnabled = enabled
  if (loggedIn !== undefined) authenticated = loggedIn
}

export function getAuthState() {
  return { authEnabled, authenticated }
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (!authEnabled) return true

  if (to.meta.requiresAuth && !authenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.guest && authenticated) {
    return { name: 'landing' }
  }

  return true
})

export default router
