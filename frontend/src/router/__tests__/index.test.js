import { describe, it, expect } from 'vitest'
import routerInstance, { routes } from '../index.js'

describe('Router — route definitions', () => {
  it('has all expected named routes', () => {
    const names = routerInstance.getRoutes().map((r) => r.name).filter(Boolean)
    expect(names).toContain('landing')
    expect(names).toContain('scenario-builder')
    expect(names).toContain('agent-profile')
    expect(names).toContain('workspace')
    expect(names).toContain('report')
    expect(names).toContain('chat')
    expect(names).toContain('settings')
    expect(names).toContain('simulations')
  })

  it('maps correct paths', () => {
    const byName = Object.fromEntries(
      routerInstance.getRoutes().filter((r) => r.name).map((r) => [r.name, r.path]),
    )
    expect(byName['landing']).toBe('/')
    expect(byName['scenario-builder']).toBe('/scenarios/:id')
    expect(byName['agent-profile']).toBe('/workspace/:taskId/agent/:agentId')
    expect(byName['workspace']).toBe('/workspace/:taskId')
    expect(byName['report']).toBe('/report/:taskId')
    expect(byName['chat']).toBe('/chat/:taskId')
    expect(byName['settings']).toBe('/settings')
    expect(byName['simulations']).toBe('/simulations')
  })

  it('includes redirect routes', () => {
    const allPaths = routerInstance.getRoutes().map((r) => r.path)
    expect(allPaths).toContain('/login')
    expect(allPaths).toContain('/graph/:taskId')
    expect(allPaths).toContain('/simulation/:taskId')
    expect(allPaths).toContain('/dashboard')
  })

  it('passes props on parameterized routes', () => {
    const paramRoutes = ['scenario-builder', 'agent-profile', 'workspace', 'report', 'chat']
    for (const name of paramRoutes) {
      const route = routerInstance.getRoutes().find((r) => r.name === name)
      expect(route.props).toBeTruthy()
    }
  })
})
