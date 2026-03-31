import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// Mock the API client before importing the module
vi.mock('../../api/client', () => ({ API_BASE: '/api' }))

describe('useOfflineMode', () => {
  let mod

  beforeEach(async () => {
    // Reset module state between tests
    vi.resetModules()
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true })))
    vi.stubGlobal('navigator', {
      onLine: true,
      connection: {
        effectiveType: '4g',
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      },
    })
    vi.useFakeTimers()
    mod = await import('../useOfflineMode.js')
  })

  afterEach(() => {
    if (mod.isInitialized()) mod.teardown()
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('reflects navigator.onLine', () => {
      const { useOfflineMode } = mod
      const { isOnline } = useOfflineMode()
      expect(isOnline.value).toBe(true)
    })

    it('exposes connectionType from navigator.connection', () => {
      const { useOfflineMode } = mod
      const { connectionType } = useOfflineMode()
      expect(connectionType.value).toBe('4g')
    })

    it('sets lastOnline when initially online', () => {
      const { useOfflineMode } = mod
      const { lastOnline } = useOfflineMode()
      expect(lastOnline.value).toBeInstanceOf(Date)
    })

    it('computes isOffline as inverse of isOnline', () => {
      const { useOfflineMode } = mod
      const { isOnline, isOffline } = useOfflineMode()
      expect(isOffline.value).toBe(!isOnline.value)
    })
  })

  describe('handleOnline / handleOffline', () => {
    it('sets isOnline to true on online event', () => {
      const { handleOffline, handleOnline, useOfflineMode } = mod
      const { isOnline } = useOfflineMode()
      handleOffline()
      expect(isOnline.value).toBe(false)
      handleOnline()
      expect(isOnline.value).toBe(true)
    })

    it('sets isOnline to false on offline event', () => {
      const { handleOffline, useOfflineMode } = mod
      const { isOnline } = useOfflineMode()
      handleOffline()
      expect(isOnline.value).toBe(false)
    })

    it('updates lastOnline when going online', () => {
      const { handleOffline, handleOnline, useOfflineMode } = mod
      const { lastOnline } = useOfflineMode()
      const before = lastOnline.value
      handleOffline()
      vi.advanceTimersByTime(1000)
      handleOnline()
      expect(lastOnline.value.getTime()).toBeGreaterThanOrEqual(before.getTime())
    })
  })

  describe('checkConnectivity', () => {
    it('sets online when fetch succeeds', async () => {
      const { handleOffline, checkConnectivity, useOfflineMode } = mod
      const { isOnline } = useOfflineMode()
      handleOffline()
      expect(isOnline.value).toBe(false)
      await checkConnectivity()
      expect(isOnline.value).toBe(true)
    })

    it('sets offline when fetch throws', async () => {
      vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('Network error'))))
      const { checkConnectivity, useOfflineMode } = mod
      const { isOnline } = useOfflineMode()
      await checkConnectivity()
      expect(isOnline.value).toBe(false)
    })

    it('fetches /api/health with HEAD method and no-store cache', async () => {
      const { checkConnectivity } = mod
      await checkConnectivity()
      expect(fetch).toHaveBeenCalledWith('/api/health', expect.objectContaining({
        method: 'HEAD',
        cache: 'no-store',
      }))
    })

    it('updates lastOnline on successful check', async () => {
      const { checkConnectivity, useOfflineMode } = mod
      const { lastOnline } = useOfflineMode()
      await checkConnectivity()
      expect(lastOnline.value).toBeInstanceOf(Date)
    })
  })

  describe('setup / teardown', () => {
    it('registers event listeners on setup', () => {
      const addSpy = vi.spyOn(window, 'addEventListener')
      mod.setup()
      expect(addSpy).toHaveBeenCalledWith('online', expect.any(Function))
      expect(addSpy).toHaveBeenCalledWith('offline', expect.any(Function))
    })

    it('removes event listeners on teardown', () => {
      mod.setup()
      const removeSpy = vi.spyOn(window, 'removeEventListener')
      mod.teardown()
      expect(removeSpy).toHaveBeenCalledWith('online', expect.any(Function))
      expect(removeSpy).toHaveBeenCalledWith('offline', expect.any(Function))
    })

    it('does not double-initialize', () => {
      const addSpy = vi.spyOn(window, 'addEventListener')
      mod.setup()
      const callCount = addSpy.mock.calls.length
      mod.setup()
      expect(addSpy.mock.calls.length).toBe(callCount)
    })

    it('starts periodic health check on setup', () => {
      mod.setup()
      fetch.mockClear()
      vi.advanceTimersByTime(30_000)
      expect(fetch).toHaveBeenCalled()
    })

    it('stops periodic health check on teardown', () => {
      mod.setup()
      mod.teardown()
      fetch.mockClear()
      vi.advanceTimersByTime(60_000)
      expect(fetch).not.toHaveBeenCalled()
    })
  })

  describe('exports', () => {
    it('exports OFFLINE_KEY symbol', () => {
      expect(typeof mod.OFFLINE_KEY).toBe('symbol')
    })

    it('exports HEALTH_INTERVAL as 30s', () => {
      expect(mod.HEALTH_INTERVAL).toBe(30_000)
    })

    it('exports HEALTH_TIMEOUT as 5s', () => {
      expect(mod.HEALTH_TIMEOUT).toBe(5_000)
    })
  })
})
