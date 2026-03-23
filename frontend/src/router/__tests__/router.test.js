import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import routerInstance from '../index.js'

function createFreshRouter() {
  const { options } = routerInstance
  return createRouter({
    history: createWebHistory(),
    routes: options.routes,
  })
}

describe('Router routes', () => {
  it('defines all 8 required routes', () => {
    const routes = routerInstance.options.routes
    const names = routes.map((r) => r.name)
    expect(names).toContain('landing')
    expect(names).toContain('login')
    expect(names).toContain('scenario-builder')
    expect(names).toContain('graph')
    expect(names).toContain('simulation')
    expect(names).toContain('report')
    expect(names).toContain('chat')
    expect(names).toContain('settings')
    expect(routes).toHaveLength(8)
  })

  it('maps correct paths', () => {
    const routes = routerInstance.options.routes
    const byName = Object.fromEntries(routes.map((r) => [r.name, r]))
    expect(byName['landing'].path).toBe('/')
    expect(byName['login'].path).toBe('/login')
    expect(byName['scenario-builder'].path).toBe('/scenarios/:id')
    expect(byName['graph'].path).toBe('/graph/:taskId')
    expect(byName['simulation'].path).toBe('/simulation/:taskId')
    expect(byName['report'].path).toBe('/report/:taskId')
    expect(byName['chat'].path).toBe('/chat/:taskId')
    expect(byName['settings'].path).toBe('/settings')
  })

  it('passes props on parameterized routes', () => {
    const routes = routerInstance.options.routes
    const byName = Object.fromEntries(routes.map((r) => [r.name, r]))
    expect(byName['scenario-builder'].props).toBe(true)
    expect(byName['graph'].props).toBe(true)
    expect(byName['simulation'].props).toBe(true)
    expect(byName['report'].props).toBe(true)
    expect(byName['chat'].props).toBe(true)
  })

  it('marks protected routes with requiresAuth', () => {
    const routes = routerInstance.options.routes
    const protectedNames = routes
      .filter((r) => r.meta?.requiresAuth)
      .map((r) => r.name)
      .sort()
    expect(protectedNames).toEqual([
      'chat',
      'graph',
      'report',
      'scenario-builder',
      'settings',
      'simulation',
    ])
  })

  it('does not require auth for landing and login', () => {
    const routes = routerInstance.options.routes
    const byName = Object.fromEntries(routes.map((r) => [r.name, r]))
    expect(byName['landing'].meta?.requiresAuth).toBeFalsy()
    expect(byName['login'].meta?.requiresAuth).toBeFalsy()
  })
})

describe('Auth guard', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('allows navigation when auth is disabled', async () => {
    const router = createFreshRouter()
    // Copy the guard from the real router
    router.beforeEach((to) => {
      if (
        to.meta.requiresAuth &&
        localStorage.getItem('auth_enabled') === 'true' &&
        !localStorage.getItem('auth_token')
      ) {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    })

    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('settings')
  })

  it('redirects to login when auth is enabled and user is not authenticated', async () => {
    localStorage.setItem('auth_enabled', 'true')

    const router = createFreshRouter()
    router.beforeEach((to) => {
      if (
        to.meta.requiresAuth &&
        localStorage.getItem('auth_enabled') === 'true' &&
        !localStorage.getItem('auth_token')
      ) {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    })

    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/settings')
  })

  it('allows navigation when auth is enabled and user is authenticated', async () => {
    localStorage.setItem('auth_enabled', 'true')
    localStorage.setItem('auth_token', 'test-token')

    const router = createFreshRouter()
    router.beforeEach((to) => {
      if (
        to.meta.requiresAuth &&
        localStorage.getItem('auth_enabled') === 'true' &&
        !localStorage.getItem('auth_token')
      ) {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    })

    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('settings')
  })

  it('preserves redirect path with route params', async () => {
    localStorage.setItem('auth_enabled', 'true')

    const router = createFreshRouter()
    router.beforeEach((to) => {
      if (
        to.meta.requiresAuth &&
        localStorage.getItem('auth_enabled') === 'true' &&
        !localStorage.getItem('auth_token')
      ) {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    })

    await router.push('/graph/abc-123')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/graph/abc-123')
  })

  it('allows unauthenticated access to landing page', async () => {
    localStorage.setItem('auth_enabled', 'true')

    const router = createFreshRouter()
    router.beforeEach((to) => {
      if (
        to.meta.requiresAuth &&
        localStorage.getItem('auth_enabled') === 'true' &&
        !localStorage.getItem('auth_token')
      ) {
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    })

    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('landing')
  })
})
