import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import LandingView from '../views/LandingView.vue'
import LoginView from '../views/LoginView.vue'

export const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingView,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guest: true },
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
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
]

export function createAppRouter() {
  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  router.beforeEach((to) => {
    if (localStorage.getItem('auth_enabled') !== 'true') return

    const auth = useAuthStore()

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    if (to.meta.guest && auth.isAuthenticated) {
      return { name: 'landing' }
    }
  })

  return router
}

export default createAppRouter()
