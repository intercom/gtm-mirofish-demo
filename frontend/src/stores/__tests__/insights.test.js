import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/insights', () => ({
  insightsApi: {
    get: vi.fn(),
    generate: vi.fn(),
    types: vi.fn(),
    chat: vi.fn(),
  },
}))

vi.mock('../../api', () => ({
  listInsights: vi.fn(),
  refreshInsights: vi.fn(),
  pinInsight: vi.fn(),
  dismissInsight: vi.fn(),
}))

import { useInsightsStore } from '../insights'
import { insightsApi } from '../../api/insights'
import { dismissInsight } from '../../api'

describe('useInsightsStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('has empty insights', () => {
      const store = useInsightsStore()
      expect(store.insights).toEqual([])
    })

    it('is not loading', () => {
      const store = useInsightsStore()
      expect(store.loading).toBe(false)
    })

    it('has no error', () => {
      const store = useInsightsStore()
      expect(store.error).toBeNull()
    })

    it('has null dataType and mode', () => {
      const store = useInsightsStore()
      expect(store.dataType).toBeNull()
      expect(store.mode).toBeNull()
    })

    it('has null activeCategory', () => {
      const store = useInsightsStore()
      expect(store.activeCategory).toBeNull()
    })
  })

  describe('hasInsights computed', () => {
    it('is false when empty', () => {
      const store = useInsightsStore()
      expect(store.hasInsights).toBe(false)
    })

    it('is true when insights exist', () => {
      const store = useInsightsStore()
      store.insights = [{ id: '1', category: 'growth' }]
      expect(store.hasInsights).toBe(true)
    })
  })

  describe('categories computed', () => {
    it('extracts unique sorted categories', () => {
      const store = useInsightsStore()
      store.insights = [
        { id: '1', category: 'growth' },
        { id: '2', category: 'adoption' },
        { id: '3', category: 'growth' },
        { id: '4', category: 'churn' },
      ]
      expect(store.categories).toEqual(['adoption', 'churn', 'growth'])
    })

    it('returns empty array when no insights', () => {
      const store = useInsightsStore()
      expect(store.categories).toEqual([])
    })
  })

  describe('filteredInsights computed', () => {
    it('returns all when no category active', () => {
      const store = useInsightsStore()
      store.insights = [
        { id: '1', category: 'growth' },
        { id: '2', category: 'churn' },
      ]
      expect(store.filteredInsights).toHaveLength(2)
    })

    it('filters by activeCategory', () => {
      const store = useInsightsStore()
      store.insights = [
        { id: '1', category: 'growth' },
        { id: '2', category: 'churn' },
        { id: '3', category: 'growth' },
      ]
      store.setCategory('growth')
      expect(store.filteredInsights).toHaveLength(2)
      expect(store.filteredInsights.every(i => i.category === 'growth')).toBe(true)
    })
  })

  describe('pinnedCount computed', () => {
    it('counts pinned insights', () => {
      const store = useInsightsStore()
      store.insights = [
        { id: '1', pinned: true },
        { id: '2', pinned: false },
        { id: '3', pinned: true },
      ]
      expect(store.pinnedCount).toBe(2)
    })

    it('is 0 when empty', () => {
      const store = useInsightsStore()
      expect(store.pinnedCount).toBe(0)
    })
  })

  describe('setCategory', () => {
    it('changes active category', () => {
      const store = useInsightsStore()
      store.setCategory('growth')
      expect(store.activeCategory).toBe('growth')
    })

    it('can be set to null to clear filter', () => {
      const store = useInsightsStore()
      store.setCategory('growth')
      store.setCategory(null)
      expect(store.activeCategory).toBeNull()
    })
  })

  describe('clear', () => {
    it('resets state', () => {
      const store = useInsightsStore()
      store.insights = [{ id: '1' }]
      store.error = 'some error'
      store.dataType = 'pipeline'
      store.mode = 'demo'

      store.clear()

      expect(store.insights).toEqual([])
      expect(store.error).toBeNull()
      expect(store.dataType).toBeNull()
      expect(store.mode).toBeNull()
    })
  })

  describe('fetchInsights', () => {
    it('stores insights on API success', async () => {
      const store = useInsightsStore()
      const mockInsights = [{ id: '1', category: 'growth' }]
      insightsApi.get.mockResolvedValue({
        data: {
          success: true,
          data: { insights: mockInsights, data_type: 'pipeline', mode: 'llm' },
        },
      })

      await store.fetchInsights({ type: 'pipeline' })

      expect(store.insights).toEqual(mockInsights)
      expect(store.dataType).toBe('pipeline')
      expect(store.mode).toBe('llm')
      expect(store.loading).toBe(false)
    })

    it('sets error on API success=false', async () => {
      const store = useInsightsStore()
      insightsApi.get.mockResolvedValue({
        data: { success: false, error: 'Bad request' },
      })

      await store.fetchInsights()

      expect(store.error).toBe('Bad request')
      expect(store.insights).toEqual([])
    })

    it('sets error on network failure', async () => {
      const store = useInsightsStore()
      insightsApi.get.mockRejectedValue(new Error('Network error'))

      await store.fetchInsights()

      expect(store.error).toBe('Network error')
      expect(store.loading).toBe(false)
    })
  })

  describe('dismiss', () => {
    it('removes insight from list', async () => {
      const store = useInsightsStore()
      store.insights = [
        { id: '1', category: 'a' },
        { id: '2', category: 'b' },
        { id: '3', category: 'c' },
      ]
      dismissInsight.mockResolvedValue({})

      await store.dismiss('2')

      expect(store.insights).toHaveLength(2)
      expect(store.insights.find(i => i.id === '2')).toBeUndefined()
    })

    it('sets error if API call fails', async () => {
      const store = useInsightsStore()
      store.insights = [{ id: '1' }]
      dismissInsight.mockRejectedValue(new Error('Dismiss failed'))

      await store.dismiss('1')

      expect(store.error).toBe('Dismiss failed')
    })
  })
})
