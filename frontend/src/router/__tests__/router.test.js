import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../stores/auth'
import { routes, createAppRouter } from '../index.js'

describe('Router routes', () => {
  it('defines all 8 required routes', () => {
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
    const byName = Object.fromEntries(routes.map((r) => [r.name, r]))
    expect(byName['scenario-builder'].props).toBe(true)
    expect(byName['graph'].props).toBe(true)
    expect(byName['simulation'].props).toBe(true)
    expect(byName['report'].props).toBe(true)
    expect(byName['chat'].props).toBe(true)
  })

  it('marks protected routes with requiresAuth', () => {
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
    const byName = Object.fromEntries(routes.map((r) => [r.name, r]))
    expect(byName['landing'].meta?.requiresAuth).toBeFalsy()
    expect(byName['login'].meta?.requiresAuth).toBeFalsy()
  })
})

describe('Auth guard', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('allows navigation when auth is disabled', async () => {
    const router = createAppRouter()
    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('settings')
  })

  it('redirects to login when auth is enabled and user is not authenticated', async () => {
    localStorage.setItem('auth_enabled', 'true')

    const router = createAppRouter()
    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/settings')
  })

  it('allows navigation when auth is enabled and user is authenticated', async () => {
    localStorage.setItem('auth_enabled', 'true')
    const auth = useAuthStore()
    auth.login('test-token', { name: 'Test User' })

    const router = createAppRouter()
    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('settings')
  })

  it('preserves redirect path with route params', async () => {
    localStorage.setItem('auth_enabled', 'true')

    const router = createAppRouter()
    await router.push('/graph/abc-123')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/graph/abc-123')
  })

  it('allows unauthenticated access to landing page', async () => {
    localStorage.setItem('auth_enabled', 'true')

    const router = createAppRouter()
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('landing')
  })
})
