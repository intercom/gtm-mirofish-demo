import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import LandingView from '../views/LandingView.vue'

export const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingView,
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, hideNav: true },
  },
  {
    path: '/scenarios/:id',
    name: 'scenario-builder',
    component: () => import('../views/ScenarioBuilderView.vue'),
    props: true,
  },
  {
    path: '/workspace/:taskId/agent/:agentId',
    name: 'agent-profile',
    component: () => import('../views/AgentProfileView.vue'),
    props: true,
  },
  {
    path: '/workspace/:taskId',
    name: 'workspace',
    component: () => import('../views/SimulationWorkspaceView.vue'),
    props: true,
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
  },
  {
    path: '/chat/:taskId',
    name: 'chat',
    component: () => import('../views/ChatView.vue'),
    props: true,
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
  },
  {
    path: '/simulations',
    name: 'simulations',
    component: () => import('../views/SimulationsView.vue'),
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
    if (to.meta.public) return true
    const auth = useAuthStore()
    if (!auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    return true
  })

  return router
}

export default createAppRouter()
