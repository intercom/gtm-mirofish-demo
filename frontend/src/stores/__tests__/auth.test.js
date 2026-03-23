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
    expect(localStorage.getItem('mirofish-token')).toBe('jwt-123')
  })

  it('logs out and clears state', () => {
    const store = useAuthStore()
    store.login('jwt-123', { email: 'test@intercom.io' })
    store.logout()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(localStorage.getItem('mirofish-token')).toBeNull()
  })

  it('restores token from localStorage', () => {
    localStorage.setItem('mirofish-token', 'persisted-token')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('persisted-token')
  })

  it('sets user info independently', () => {
    const store = useAuthStore()
    store.setUser({ email: 'admin@intercom.io', role: 'admin' })
    expect(store.user).toEqual({ email: 'admin@intercom.io', role: 'admin' })
  })
})
