import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNavigationStore } from '../navigation'

describe('useNavigationStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial navLinks has default links', () => {
    const store = useNavigationStore()
    expect(store.navLinks.length).toBeGreaterThan(0)
  })

  it('has expected nav items', () => {
    const store = useNavigationStore()
    const ids = store.navLinks.map(l => l.id)
    expect(ids).toContain('home')
    expect(ids).toContain('dashboard')
    expect(ids).toContain('scenarios')
    expect(ids).toContain('settings')
    expect(ids).toContain('simulations')
    expect(ids).toContain('knowledge-graph')
  })

  it('home link points to / with exact true', () => {
    const store = useNavigationStore()
    const home = store.navLinks.find(l => l.id === 'home')
    expect(home.to).toBe('/')
    expect(home.exact).toBe(true)
  })

  it('resetOrder() restores default order', () => {
    const store = useNavigationStore()
    const originalIds = store.navLinks.map(l => l.id)

    store.navLinks = [...store.navLinks].reverse()
    expect(store.navLinks.map(l => l.id)).not.toEqual(originalIds)

    store.resetOrder()
    expect(store.navLinks.map(l => l.id)).toEqual(originalIds)
  })

  it('loads saved order from localStorage on init', () => {
    const store = useNavigationStore()
    const defaultIds = store.navLinks.map(l => l.id)
    const reversed = [...defaultIds].reverse()

    localStorage.setItem('mirofish_nav_order', JSON.stringify(reversed))
    setActivePinia(createPinia())
    const store2 = useNavigationStore()
    expect(store2.navLinks.map(l => l.id)).toEqual(reversed)
  })

  it('ignores corrupted localStorage data', () => {
    localStorage.setItem('mirofish_nav_order', '{broken json')
    setActivePinia(createPinia())
    const store = useNavigationStore()
    expect(store.navLinks.length).toBeGreaterThan(0)
    expect(store.navLinks[0].id).toBe('home')
  })

  it('ignores localStorage with wrong number of items', () => {
    localStorage.setItem('mirofish_nav_order', JSON.stringify(['home', 'dashboard']))
    setActivePinia(createPinia())
    const store = useNavigationStore()
    expect(store.navLinks[0].id).toBe('home')
    expect(store.navLinks.length).toBeGreaterThan(2)
  })

  it('ignores localStorage with unknown ids', () => {
    const store = useNavigationStore()
    const ids = store.navLinks.map(l => l.id)
    ids[0] = 'unknown-id'
    localStorage.setItem('mirofish_nav_order', JSON.stringify(ids))
    setActivePinia(createPinia())
    const store2 = useNavigationStore()
    expect(store2.navLinks[0].id).toBe('home')
  })
})
