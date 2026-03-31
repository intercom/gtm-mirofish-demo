import { describe, it, expect } from 'vitest'
import { routes, createAppRouter } from '../index.js'

describe('Router routes', () => {
  it('defines all expected routes', () => {
    const names = routes.map((r) => r.name).filter(Boolean)
    expect(names).toContain('landing')
    expect(names).toContain('scenario-builder')
    expect(names).toContain('agent-profile')
    expect(names).toContain('workspace')
    expect(names).toContain('report')
    expect(names).toContain('chat')
    expect(names).toContain('settings')
    expect(names).toContain('simulations')
    expect(routes).toHaveLength(12)
  })

  it('maps correct paths', () => {
    const byName = Object.fromEntries(routes.filter((r) => r.name).map((r) => [r.name, r]))
    expect(byName['landing'].path).toBe('/')
    expect(byName['scenario-builder'].path).toBe('/scenarios/:id')
    expect(byName['agent-profile'].path).toBe('/workspace/:taskId/agent/:agentId')
    expect(byName['workspace'].path).toBe('/workspace/:taskId')
    expect(byName['report'].path).toBe('/report/:taskId')
    expect(byName['chat'].path).toBe('/chat/:taskId')
    expect(byName['settings'].path).toBe('/settings')
    expect(byName['simulations'].path).toBe('/simulations')
  })

  it('passes props on parameterized routes', () => {
    const byName = Object.fromEntries(routes.filter((r) => r.name).map((r) => [r.name, r]))
    expect(byName['scenario-builder'].props).toBe(true)
    expect(byName['agent-profile'].props).toBe(true)
    expect(byName['workspace'].props).toBe(true)
    expect(byName['report'].props).toBe(true)
    expect(byName['chat'].props).toBe(true)
  })

  it('includes redirect routes for legacy paths', () => {
    const redirectRoutes = routes.filter((r) => r.redirect)
    const redirectPaths = redirectRoutes.map((r) => r.path)
    expect(redirectPaths).toContain('/login')
    expect(redirectPaths).toContain('/graph/:taskId')
    expect(redirectPaths).toContain('/simulation/:taskId')
    expect(redirectPaths).toContain('/dashboard')
  })
})

describe('createAppRouter', () => {
  it('creates a working router instance', async () => {
    const router = createAppRouter()
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('landing')
  })

  it('resolves settings route', async () => {
    const router = createAppRouter()
    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('settings')
  })
})
