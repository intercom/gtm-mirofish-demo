import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('initializes as unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
  })

  it('logs in with token and user info', () => {
    const store = useAuthStore()
    store.login('jwt-123', { email: 'test@intercom.io', name: 'Test' })
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('jwt-123')
    expect(store.user).toEqual({ email: 'test@intercom.io', name: 'Test' })
    expect(localStorage.getItem('auth_token')).toBe('jwt-123')
    expect(JSON.parse(localStorage.getItem('mirofish-user'))).toEqual({ email: 'test@intercom.io', name: 'Test' })
  })

  it('logs out and clears state', () => {
    const store = useAuthStore()
    store.login('jwt-123', { email: 'test@intercom.io' })
    store.logout()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(localStorage.getItem('mirofish-user')).toBeNull()
  })

  it('restores token from localStorage', () => {
    localStorage.setItem('auth_token', 'persisted-token')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('persisted-token')
  })

  it('restores user from localStorage', () => {
    localStorage.setItem('auth_token', 'persisted-token')
    localStorage.setItem('mirofish-user', JSON.stringify({ email: 'a@intercom.io' }))
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.user).toEqual({ email: 'a@intercom.io' })
  })

  it('sets user info independently and persists it', () => {
    const store = useAuthStore()
    store.setUser({ email: 'admin@intercom.io', role: 'admin' })
    expect(store.user).toEqual({ email: 'admin@intercom.io', role: 'admin' })
    expect(JSON.parse(localStorage.getItem('mirofish-user'))).toEqual({ email: 'admin@intercom.io', role: 'admin' })
  })

  it('clears persisted user when setUser is called with null', () => {
    const store = useAuthStore()
    store.setUser({ email: 'admin@intercom.io' })
    store.setUser(null)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('mirofish-user')).toBeNull()
  })
})
