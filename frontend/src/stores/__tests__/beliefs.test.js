import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/beliefs', () => ({
  beliefsApi: {
    getDimensions: vi.fn(),
    extract: vi.fn(),
    demo: vi.fn(),
  },
}))

import { useBeliefsStore } from '../beliefs'
import { beliefsApi } from '../../api/beliefs'

describe('useBeliefsStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('has empty rounds', () => {
      const store = useBeliefsStore()
      expect(store.rounds).toEqual([])
    })

    it('has empty dimensions', () => {
      const store = useBeliefsStore()
      expect(store.dimensions).toEqual([])
    })

    it('has null mode', () => {
      const store = useBeliefsStore()
      expect(store.mode).toBeNull()
    })

    it('is not loading', () => {
      const store = useBeliefsStore()
      expect(store.loading).toBe(false)
    })

    it('has no error', () => {
      const store = useBeliefsStore()
      expect(store.error).toBeNull()
    })
  })

  describe('hasData computed', () => {
    it('is false when empty', () => {
      const store = useBeliefsStore()
      expect(store.hasData).toBe(false)
    })

    it('is true when has rounds', () => {
      const store = useBeliefsStore()
      store.rounds = [{ round: 1, beliefs: [] }]
      expect(store.hasData).toBe(true)
    })
  })

  describe('latestRound computed', () => {
    it('is null when empty', () => {
      const store = useBeliefsStore()
      expect(store.latestRound).toBeNull()
    })

    it('returns last element when has data', () => {
      const store = useBeliefsStore()
      store.rounds = [
        { round: 1, beliefs: ['a'] },
        { round: 2, beliefs: ['b'] },
        { round: 3, beliefs: ['c'] },
      ]
      expect(store.latestRound).toEqual({ round: 3, beliefs: ['c'] })
    })
  })

  describe('extractBeliefs', () => {
    it('stores rounds and mode on API success', async () => {
      const store = useBeliefsStore()
      const mockRounds = [{ round: 1, beliefs: [] }, { round: 2, beliefs: [] }]
      beliefsApi.extract.mockResolvedValue({
        data: { rounds: mockRounds, mode: 'keyword' },
      })

      await store.extractBeliefs('sim-1', ['action1'], false)

      expect(beliefsApi.extract).toHaveBeenCalledWith('sim-1', ['action1'], false)
      expect(store.rounds).toEqual(mockRounds)
      expect(store.mode).toBe('keyword')
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error message on API error', async () => {
      const store = useBeliefsStore()
      beliefsApi.extract.mockRejectedValue(new Error('Extraction failed'))

      await store.extractBeliefs('sim-1', [], false)

      expect(store.error).toBe('Extraction failed')
      expect(store.loading).toBe(false)
      expect(store.rounds).toEqual([])
    })

    it('uses fallback error message when error has no message', async () => {
      const store = useBeliefsStore()
      beliefsApi.extract.mockRejectedValue(new Error())

      await store.extractBeliefs('sim-1', [], false)

      expect(store.error).toBe('Failed to extract beliefs')
    })
  })

  describe('fetchDemo', () => {
    it('sets mode to demo on success', async () => {
      const store = useBeliefsStore()
      const mockRounds = [{ round: 1 }]
      beliefsApi.demo.mockResolvedValue({ data: { rounds: mockRounds } })

      await store.fetchDemo(5)

      expect(beliefsApi.demo).toHaveBeenCalledWith(5)
      expect(store.rounds).toEqual(mockRounds)
      expect(store.mode).toBe('demo')
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      const store = useBeliefsStore()
      beliefsApi.demo.mockRejectedValue(new Error('Demo failed'))

      await store.fetchDemo()

      expect(store.error).toBe('Demo failed')
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchDimensions', () => {
    it('stores dimensions from API', async () => {
      const store = useBeliefsStore()
      const mockDims = [{ key: 'quality', label: 'Quality' }]
      beliefsApi.getDimensions.mockResolvedValue({ data: { dimensions: mockDims } })

      await store.fetchDimensions()

      expect(store.dimensions).toEqual(mockDims)
    })

    it('uses fallback dimensions on error (5 items)', async () => {
      const store = useBeliefsStore()
      beliefsApi.getDimensions.mockRejectedValue(new Error('fail'))

      await store.fetchDimensions()

      expect(store.dimensions).toHaveLength(5)
      expect(store.dimensions[0].key).toBe('product_quality')
      expect(store.dimensions[1].key).toBe('pricing')
      expect(store.dimensions[2].key).toBe('brand_trust')
      expect(store.dimensions[3].key).toBe('competitive_position')
      expect(store.dimensions[4].key).toBe('adoption_intent')
    })
  })

  describe('reset', () => {
    it('clears all state', async () => {
      const store = useBeliefsStore()
      store.rounds = [{ round: 1 }]
      store.mode = 'llm'
      store.loading = true
      store.error = 'some error'

      store.reset()

      expect(store.rounds).toEqual([])
      expect(store.mode).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
