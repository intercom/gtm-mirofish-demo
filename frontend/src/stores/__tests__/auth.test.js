import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('initialises as unauthenticated', () => {
    const store = useAuthStore()
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('setAuth stores user and token', () => {
    const store = useAuthStore()
    store.setAuth({ name: 'Alice', email: 'alice@intercom.io' }, 'tok-123')
    expect(store.isAuthenticated).toBe(true)
    expect(store.user.name).toBe('Alice')
    expect(store.token).toBe('tok-123')
  })

  it('persists auth to localStorage', () => {
    const store = useAuthStore()
    store.setAuth({ name: 'Bob' }, 'tok-456')
    const saved = JSON.parse(localStorage.getItem('mirofish-auth'))
    expect(saved.user.name).toBe('Bob')
    expect(saved.token).toBe('tok-456')
  })

  it('loads auth from localStorage on init', () => {
    localStorage.setItem('mirofish-auth', JSON.stringify({
      user: { name: 'Carol' },
      token: 'tok-789',
    }))
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.user.name).toBe('Carol')
    expect(store.isAuthenticated).toBe(true)
  })

  it('logout clears state and localStorage', () => {
    const store = useAuthStore()
    store.setAuth({ name: 'Dave' }, 'tok-abc')
    store.logout()
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('mirofish-auth')).toBeNull()
  })

  it('checkAuth returns false when no token', async () => {
    const store = useAuthStore()
    const result = await store.checkAuth()
    expect(result).toBe(false)
  })

  it('checkAuth validates token against API', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ user: { name: 'Eve', email: 'eve@intercom.io' } }),
    }))
    const store = useAuthStore()
    store.setAuth({ name: 'temp' }, 'tok-valid')
    const result = await store.checkAuth()
    expect(result).toBe(true)
    expect(store.user.name).toBe('Eve')
    vi.unstubAllGlobals()
  })

  it('checkAuth logs out on 401', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
    const store = useAuthStore()
    store.setAuth({ name: 'temp' }, 'tok-expired')
    const result = await store.checkAuth()
    expect(result).toBe(false)
    expect(store.isAuthenticated).toBe(false)
    vi.unstubAllGlobals()
  })

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem('mirofish-auth', '{bad-json')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })
})
