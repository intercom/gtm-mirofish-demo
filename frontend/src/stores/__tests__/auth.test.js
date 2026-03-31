import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

vi.mock('../../api/auth', () => ({
  authApi: {
    me: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}))

import { authApi } from '../../api/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
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
    authApi.me.mockResolvedValue({
      data: { user: { name: 'Eve', email: 'eve@intercom.io' } },
    })
    const store = useAuthStore()
    store.setAuth({ name: 'temp' }, 'tok-valid')
    const result = await store.checkAuth()
    expect(result).toBe(true)
    expect(store.user.name).toBe('Eve')
  })

  it('checkAuth logs out on API error', async () => {
    authApi.me.mockRejectedValue({ message: 'Unauthorized', status: 401 })
    const store = useAuthStore()
    store.setAuth({ name: 'temp' }, 'tok-expired')
    const result = await store.checkAuth()
    expect(result).toBe(false)
    expect(store.isAuthenticated).toBe(false)
  })

  it('login calls API and stores result', async () => {
    authApi.login.mockResolvedValue({
      data: { user: { name: 'Frank', email: 'frank@intercom.io' }, token: 'tok-new' },
    })
    const store = useAuthStore()
    const user = await store.login({ email: 'frank@intercom.io' })
    expect(user.name).toBe('Frank')
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('tok-new')
  })

  it('logoutAndNotify calls API then clears state', async () => {
    authApi.logout.mockResolvedValue({ data: { ok: true } })
    const store = useAuthStore()
    store.setAuth({ name: 'Grace' }, 'tok-bye')
    await store.logoutAndNotify()
    expect(store.isAuthenticated).toBe(false)
    expect(authApi.logout).toHaveBeenCalled()
  })

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem('mirofish-auth', '{bad-json')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('tracks loading state during checkAuth', async () => {
    let resolveMe
    authApi.me.mockReturnValue(new Promise((r) => { resolveMe = r }))
    const store = useAuthStore()
    store.setAuth({ name: 'temp' }, 'tok-123')
    const promise = store.checkAuth()
    expect(store.loading).toBe(true)
    resolveMe({ data: { user: { name: 'Heidi' } } })
    await promise
    expect(store.loading).toBe(false)
  })
})
