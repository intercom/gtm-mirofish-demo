import { describe, it, expect, beforeEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import routerInstance, { setAuthState, getAuthState } from '../index.js'

function createTestRouter() {
  const routes = routerInstance.getRoutes().map((r) => ({
    path: r.path,
    name: r.name,
    component: r.components?.default ?? { template: '<div />' },
    meta: r.meta,
    props: r.props,
  }))

  const router = createRouter({
    history: createWebHistory(),
    routes,
  })

  // Copy the beforeEach guard from the real router
  router.beforeEach((to) => {
    const { authEnabled, authenticated } = getAuthState()

    if (!authEnabled) return true

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

describe('Router — route definitions', () => {
  it('has all expected routes', () => {
    const names = routerInstance.getRoutes().map((r) => r.name)
    expect(names).toContain('landing')
    expect(names).toContain('scenario-builder')
    expect(names).toContain('graph')
    expect(names).toContain('simulation')
    expect(names).toContain('report')
    expect(names).toContain('chat')
    expect(names).toContain('settings')
    expect(names).toContain('login')
  })

  it('maps correct paths', () => {
    const byName = Object.fromEntries(
      routerInstance.getRoutes().map((r) => [r.name, r.path]),
    )
    expect(byName['landing']).toBe('/')
    expect(byName['scenario-builder']).toBe('/scenarios/:id')
    expect(byName['graph']).toBe('/graph/:taskId')
    expect(byName['simulation']).toBe('/simulation/:taskId')
    expect(byName['report']).toBe('/report/:taskId')
    expect(byName['chat']).toBe('/chat/:taskId')
    expect(byName['settings']).toBe('/settings')
    expect(byName['login']).toBe('/login')
  })

  it('marks protected routes with requiresAuth meta', () => {
    const protectedNames = routerInstance
      .getRoutes()
      .filter((r) => r.meta.requiresAuth)
      .map((r) => r.name)

    expect(protectedNames).toEqual(
      expect.arrayContaining([
        'scenario-builder',
        'graph',
        'simulation',
        'report',
        'chat',
        'settings',
      ]),
    )
    expect(protectedNames).not.toContain('landing')
    expect(protectedNames).not.toContain('login')
  })

  it('marks login as guest-only', () => {
    const login = routerInstance.getRoutes().find((r) => r.name === 'login')
    expect(login.meta.guest).toBe(true)
  })

  it('passes props on parameterized routes', () => {
    const paramRoutes = ['scenario-builder', 'graph', 'simulation', 'report', 'chat']
    for (const name of paramRoutes) {
      const route = routerInstance.getRoutes().find((r) => r.name === name)
      expect(route.props).toBeTruthy()
    }
  })
})

describe('Router — auth guard', () => {
  let router

  beforeEach(() => {
    setAuthState({ enabled: false, loggedIn: false })
    router = createTestRouter()
  })

  it('allows all navigation when auth is disabled', async () => {
    setAuthState({ enabled: false, loggedIn: false })
    await router.push('/settings')
    expect(router.currentRoute.value.name).toBe('settings')
  })

  it('redirects unauthenticated users to login when auth is enabled', async () => {
    setAuthState({ enabled: true, loggedIn: false })
    await router.push('/settings')
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/settings')
  })

  it('preserves redirect path in query param', async () => {
    setAuthState({ enabled: true, loggedIn: false })
    await router.push('/graph/task-123')
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/graph/task-123')
  })

  it('allows authenticated users to access protected routes', async () => {
    setAuthState({ enabled: true, loggedIn: true })
    await router.push('/settings')
    expect(router.currentRoute.value.name).toBe('settings')
  })

  it('redirects authenticated users away from login page', async () => {
    setAuthState({ enabled: true, loggedIn: true })
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('landing')
  })

  it('allows unauthenticated users to visit landing page', async () => {
    setAuthState({ enabled: true, loggedIn: false })
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('landing')
  })

  it('allows unauthenticated users to visit login page', async () => {
    setAuthState({ enabled: true, loggedIn: false })
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('login')
  })
})

describe('Auth state helpers', () => {
  beforeEach(() => {
    setAuthState({ enabled: false, loggedIn: false })
  })

  it('returns current auth state', () => {
    expect(getAuthState()).toEqual({ authEnabled: false, authenticated: false })
  })

  it('updates auth enabled flag', () => {
    setAuthState({ enabled: true })
    expect(getAuthState().authEnabled).toBe(true)
  })

  it('updates authenticated flag', () => {
    setAuthState({ loggedIn: true })
    expect(getAuthState().authenticated).toBe(true)
  })

  it('handles partial updates', () => {
    setAuthState({ enabled: true, loggedIn: true })
    setAuthState({ loggedIn: false })
    expect(getAuthState()).toEqual({ authEnabled: true, authenticated: false })
  })
})
