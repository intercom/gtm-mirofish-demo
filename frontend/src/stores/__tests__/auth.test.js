import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

describe('useAuthStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useAuthStore()
    vi.restoreAllMocks()
  })

  it('initializes with null user and no loading/error', () => {
    expect(store.user).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  describe('fetchUser', () => {
    it('sets user on successful response', async () => {
      const mockUser = { email: 'test@intercom.io', name: 'Test User' }
      vi.spyOn(globalThis, 'fetch').mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockUser),
      })

      await store.fetchUser()

      expect(store.user).toEqual(mockUser)
      expect(store.loading).toBe(false)
      expect(fetch).toHaveBeenCalledWith('/api/auth/me')
    })

    it('sets user to null on non-ok response', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false })

      await store.fetchUser()

      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('sets user to null on network error', async () => {
      vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network error'))

      await store.fetchUser()

      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
    })

    it('sets loading to true while fetching', async () => {
      let resolveFetch
      vi.spyOn(globalThis, 'fetch').mockImplementation(
        () => new Promise((resolve) => { resolveFetch = resolve })
      )

      const promise = store.fetchUser()
      expect(store.loading).toBe(true)

      resolveFetch({ ok: false })
      await promise
      expect(store.loading).toBe(false)
    })
  })

  describe('loginWithGoogle', () => {
    it('redirects to /api/auth/google', () => {
      const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
        ...window.location,
        href: '',
        set href(val) { this._href = val },
        get _href() { return '' },
      })

      // We need to test the assignment, so mock differently
      delete window.location
      window.location = { href: '' }

      store.loginWithGoogle()
      expect(window.location.href).toBe('/api/auth/google')

      // Restore
      window.location = locationSpy.getMockImplementation()?.() || { href: '' }
      locationSpy.mockRestore()
    })
  })

  describe('loginWithOkta', () => {
    it('redirects to /api/auth/okta', () => {
      delete window.location
      window.location = { href: '' }

      store.loginWithOkta()
      expect(window.location.href).toBe('/api/auth/okta')
    })
  })

  describe('logout', () => {
    it('calls logout endpoint and clears user', async () => {
      store.user = { email: 'test@intercom.io' }
      vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: true })

      await store.logout()

      expect(store.user).toBeNull()
      expect(fetch).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' })
    })

    it('clears user even if logout request fails', async () => {
      store.user = { email: 'test@intercom.io' }
      vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network error'))

      await store.logout()

      expect(store.user).toBeNull()
    })
  })
})
