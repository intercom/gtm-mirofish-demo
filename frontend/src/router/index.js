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
    path: '/workspace/:taskId/agent/:agentId',
    name: 'agent-profile',
    component: () => import('../views/AgentProfileView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/workspace/:taskId',
    name: 'workspace',
    component: () => import('../views/SimulationWorkspaceView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/graph/:taskId',
    redirect: (to) => `/workspace/${to.params.taskId}?tab=graph`,
  },
  {
    path: '/simulation/:taskId',
    redirect: (to) => `/workspace/${to.params.taskId}?tab=simulation`,
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
    path: '/simulations',
    name: 'simulations',
    component: () => import('../views/SimulationsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    redirect: '/simulations',
  },
]

export function createAppRouter() {
  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  router.beforeEach((to) => {
    // Auth is enforced if EITHER the build-time env var OR localStorage flag is set
    const authRequired = import.meta.env.VITE_AUTH_ENABLED === 'true' || localStorage.getItem('auth_enabled') === 'true'
    if (!authRequired) return

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
