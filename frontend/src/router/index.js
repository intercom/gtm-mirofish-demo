import { createRouter, createWebHistory } from 'vue-router'

import LandingView from '../views/LandingView.vue'

export const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingView,
  },
  {
    path: '/login',
    redirect: '/',
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
    name: 'gtm-dashboard',
    component: () => import('../views/GtmDashboardView.vue'),
  },
]

export function createAppRouter() {
  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  return router
}

export default createAppRouter()
