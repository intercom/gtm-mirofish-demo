import { createRouter, createWebHistory } from 'vue-router'

// Module-level auth state — decoupled from Pinia so the navigation
// guard works before the Vue app (and stores) are fully initialised.
let _authEnabled = false
let _authenticated = false

export function setAuthState({ enabled, loggedIn } = {}) {
  if (enabled !== undefined) _authEnabled = enabled
  if (loggedIn !== undefined) _authenticated = loggedIn
}

export function getAuthState() {
  return { authEnabled: _authEnabled, authenticated: _authenticated }
}

export const routes = [
  {
    path: '/',
    name: 'landing',
    component: () => import('../views/LandingView.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, guest: true, hideNav: true },
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
    name: 'graph',
    component: () => import('../views/SimulationWorkspaceView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/simulation/:taskId',
    name: 'simulation',
    component: () => import('../views/SimulationWorkspaceView.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/report/new',
    name: 'report-wizard',
    component: () => import('../views/ReportWizardView.vue'),
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
    path: '/knowledge-graph/:graphId?',
    name: 'knowledge-graph',
    component: () => import('../views/KnowledgeGraphView.vue'),
    props: true,
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
    const { authEnabled, authenticated } = getAuthState()

    if (!authEnabled) return true

    if (to.meta.public && !(to.meta.guest && authenticated)) return true

    if (to.meta.requiresAuth && !authenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }

    if (to.meta.guest && authenticated) {
      return { name: 'landing' }
    }

    return true
  })

  return router
}

export default createAppRouter()
