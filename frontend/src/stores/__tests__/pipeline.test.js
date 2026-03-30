import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/pipeline', () => ({
  pipelineApi: {
    getFunnel: vi.fn(),
    getFunnelHistory: vi.fn(),
    getConversions: vi.fn(),
    getVelocity: vi.fn(),
    getForecast: vi.fn(),
  },
}))

import { usePipelineStore } from '../pipeline'
import { pipelineApi } from '../../api/pipeline'

describe('usePipelineStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('has null funnelData', () => {
      const store = usePipelineStore()
      expect(store.funnelData).toBeNull()
    })

    it('has empty funnelHistory', () => {
      const store = usePipelineStore()
      expect(store.funnelHistory).toEqual([])
    })

    it('has null conversions, velocity, and forecast', () => {
      const store = usePipelineStore()
      expect(store.conversions).toBeNull()
      expect(store.velocity).toBeNull()
      expect(store.forecast).toBeNull()
    })

    it('is not loading and has no error', () => {
      const store = usePipelineStore()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('computed', () => {
    it('overallConversionRate is 0 when no data', () => {
      const store = usePipelineStore()
      expect(store.overallConversionRate).toBe(0)
    })

    it('overallConversionRate returns conversions.overall', () => {
      const store = usePipelineStore()
      store.conversions = { overall: 0.0159 }
      expect(store.overallConversionRate).toBe(0.0159)
    })

    it('avgCycleTime is 0 when no data', () => {
      const store = usePipelineStore()
      expect(store.avgCycleTime).toBe(0)
    })

    it('avgCycleTime returns velocity.avgCycleDays', () => {
      const store = usePipelineStore()
      store.velocity = { avgCycleDays: 34 }
      expect(store.avgCycleTime).toBe(34)
    })

    it('totalPipelineValue is 0 when no funnelData', () => {
      const store = usePipelineStore()
      expect(store.totalPipelineValue).toBe(0)
    })

    it('totalPipelineValue sums non-Closed Won stage values', () => {
      const store = usePipelineStore()
      store.funnelData = {
        stages: [
          { name: 'Leads', count: 100, value: 5000000 },
          { name: 'MQL', count: 50, value: 3000000 },
          { name: 'Closed Won', count: 10, value: 1000000 },
        ],
      }
      expect(store.totalPipelineValue).toBe(8000000)
    })

    it('forecastedRevenue is 0 when no forecast', () => {
      const store = usePipelineStore()
      expect(store.forecastedRevenue).toBe(0)
    })

    it('forecastedRevenue returns forecast.projected', () => {
      const store = usePipelineStore()
      store.forecast = { projected: 7200000 }
      expect(store.forecastedRevenue).toBe(7200000)
    })
  })

  describe('fetchFunnel', () => {
    it('returns cached data when not forced', async () => {
      const store = usePipelineStore()
      const cached = { stages: [{ name: 'Leads', count: 100, value: 500 }] }
      store.funnelData = cached

      const result = await store.fetchFunnel()

      expect(pipelineApi.getFunnel).not.toHaveBeenCalled()
      expect(result).toEqual(cached)
    })

    it('fetches from API on first call', async () => {
      const store = usePipelineStore()
      const apiData = { stages: [{ name: 'Leads', count: 200, value: 1000 }] }
      pipelineApi.getFunnel.mockResolvedValue({ data: apiData })

      const result = await store.fetchFunnel()

      expect(pipelineApi.getFunnel).toHaveBeenCalledOnce()
      expect(result).toEqual(apiData)
      expect(store.funnelData).toEqual(apiData)
    })

    it('falls back to demo data on error', async () => {
      const store = usePipelineStore()
      pipelineApi.getFunnel.mockRejectedValue(new Error('Network error'))

      const result = await store.fetchFunnel()

      expect(result).toBeTruthy()
      expect(result.stages).toHaveLength(6)
      expect(result.stages[0].name).toBe('Leads')
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchConversions', () => {
    it('falls back to demo data on error', async () => {
      const store = usePipelineStore()
      pipelineApi.getConversions.mockRejectedValue(new Error('fail'))

      const result = await store.fetchConversions()

      expect(result).toBeTruthy()
      expect(result.overall).toBe(0.0159)
      expect(result.byStage).toHaveLength(5)
    })

    it('stores API data on success', async () => {
      const store = usePipelineStore()
      const apiData = { overall: 0.05, byStage: [] }
      pipelineApi.getConversions.mockResolvedValue({ data: apiData })

      const result = await store.fetchConversions()

      expect(result).toEqual(apiData)
      expect(store.conversions).toEqual(apiData)
    })
  })

  describe('fetchVelocity', () => {
    it('falls back to demo data on error', async () => {
      const store = usePipelineStore()
      pipelineApi.getVelocity.mockRejectedValue(new Error('fail'))

      const result = await store.fetchVelocity()

      expect(result).toBeTruthy()
      expect(result.avgCycleDays).toBe(34)
    })

    it('stores API data on success', async () => {
      const store = usePipelineStore()
      const apiData = { avgCycleDays: 28, byStage: [] }
      pipelineApi.getVelocity.mockResolvedValue({ data: apiData })

      const result = await store.fetchVelocity()

      expect(result).toEqual(apiData)
      expect(store.velocity).toEqual(apiData)
    })
  })

  describe('fetchForecast', () => {
    it('falls back to demo data on error', async () => {
      const store = usePipelineStore()
      pipelineApi.getForecast.mockRejectedValue(new Error('fail'))

      const result = await store.fetchForecast()

      expect(result).toBeTruthy()
      expect(result.projected).toBe(7200000)
    })

    it('stores API data on success', async () => {
      const store = usePipelineStore()
      const apiData = { current: 1000000, projected: 2000000 }
      pipelineApi.getForecast.mockResolvedValue({ data: apiData })

      const result = await store.fetchForecast()

      expect(result).toEqual(apiData)
      expect(store.forecast).toEqual(apiData)
    })
  })

  describe('reset', () => {
    it('clears all state', async () => {
      const store = usePipelineStore()
      store.funnelData = { stages: [] }
      store.funnelHistory = [{ month: '2025-01' }]
      store.conversions = { overall: 0.05 }
      store.velocity = { avgCycleDays: 30 }
      store.forecast = { projected: 100 }
      store.loading = true
      store.error = 'some error'

      store.reset()

      expect(store.funnelData).toBeNull()
      expect(store.funnelHistory).toEqual([])
      expect(store.conversions).toBeNull()
      expect(store.velocity).toBeNull()
      expect(store.forecast).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
