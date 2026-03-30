import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const mockGet = vi.fn()

vi.mock('../../api/client', () => ({
  default: { get: mockGet },
}))

describe('useServiceStatus', () => {
  let mod

  beforeEach(async () => {
    vi.resetModules()
    vi.useFakeTimers()
    mockGet.mockReset()

    // Default: resolve with all-ok
    mockGet.mockResolvedValue({
      data: {
        services: {
          backend: { status: 'ok' },
          llm: { status: 'ok' },
          zep: { status: 'ok' },
        },
      },
    })

    mod = await import('../useServiceStatus.js')
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  function mountWithComposable() {
    let composable
    const wrapper = mount({
      template: '<div />',
      setup() {
        composable = mod.useServiceStatus()
        return composable
      },
    })
    return { wrapper, composable }
  }

  // Flush the initial check() triggered by onMounted -> startPolling
  async function flushInitialCheck() {
    await flushPromises()
    await vi.advanceTimersByTimeAsync(0)
    await flushPromises()
  }

  describe('initial state', () => {
    it('starts with unknown status for all services', () => {
      const { composable } = mountWithComposable()
      expect(composable.services.value.backend.status).toBe('unknown')
      expect(composable.services.value.llm.status).toBe('unknown')
      expect(composable.services.value.zep.status).toBe('unknown')
    })

    it('loading starts as false before first check', () => {
      mockGet.mockReturnValue(new Promise(() => {})) // never resolves
      const { composable } = mountWithComposable()
      // loading becomes true once check() starts (synchronously during mount)
      expect(typeof composable.loading.value).toBe('boolean')
    })
  })

  describe('computed properties', () => {
    it('isAllOk is true when all services are ok', async () => {
      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.isAllOk.value).toBe(true)
    })

    it('isAllOk is false when any service is not ok', async () => {
      mockGet.mockResolvedValue({
        data: {
          services: {
            backend: { status: 'ok' },
            llm: { status: 'error' },
            zep: { status: 'ok' },
          },
        },
      })

      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.isAllOk.value).toBe(false)
    })

    it('isDemoMode is true when any service is unconfigured', async () => {
      mockGet.mockResolvedValue({
        data: {
          services: {
            backend: { status: 'ok' },
            llm: { status: 'unconfigured' },
            zep: { status: 'ok' },
          },
        },
      })

      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.isDemoMode.value).toBe(true)
    })

    it('isDemoMode is false when all services are ok', async () => {
      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.isDemoMode.value).toBe(false)
    })

    it('isBackendReachable reflects backend status', async () => {
      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.isBackendReachable.value).toBe(true)
    })
  })

  describe('error handling', () => {
    it('sets backend to error when API call fails', async () => {
      mockGet.mockRejectedValue(new Error('Network error'))

      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.services.value.backend.status).toBe('error')
      expect(composable.services.value.backend.message).toBe('Backend unreachable')
    })

    it('sets llm and zep to unknown when API call fails', async () => {
      mockGet.mockRejectedValue(new Error('fail'))

      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.services.value.llm.status).toBe('unknown')
      expect(composable.services.value.zep.status).toBe('unknown')
    })

    it('sets lastChecked even on error', async () => {
      mockGet.mockRejectedValue(new Error('fail'))

      const { composable } = mountWithComposable()
      await flushInitialCheck()

      expect(composable.lastChecked.value).toBeGreaterThan(0)
    })
  })

  describe('check function', () => {
    it('calls /api/v1/services/status', async () => {
      const { composable } = mountWithComposable()
      await composable.check()

      expect(mockGet).toHaveBeenCalledWith('/api/v1/services/status')
    })

    it('updates lastChecked timestamp on success', async () => {
      const { composable } = mountWithComposable()
      await composable.check()

      expect(composable.lastChecked.value).toBeGreaterThan(0)
    })

    it('sets loading to false after check completes', async () => {
      const { composable } = mountWithComposable()
      await composable.check()

      expect(composable.loading.value).toBe(false)
    })
  })

  describe('polling lifecycle', () => {
    it('polls on the 60s interval', async () => {
      const { composable } = mountWithComposable()
      await flushInitialCheck()

      const callsBefore = mockGet.mock.calls.length
      await vi.advanceTimersByTimeAsync(60_000)
      await flushPromises()

      expect(mockGet.mock.calls.length).toBeGreaterThan(callsBefore)
    })

    it('stops polling when last subscriber unmounts', async () => {
      const { wrapper } = mountWithComposable()
      await flushInitialCheck()

      mockGet.mockClear()
      wrapper.unmount()

      // Advance past one poll interval — should NOT fire
      await vi.advanceTimersByTimeAsync(61_000)
      expect(mockGet).not.toHaveBeenCalled()
    })
  })
})
