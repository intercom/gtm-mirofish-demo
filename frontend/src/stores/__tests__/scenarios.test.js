import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useScenariosStore } from '../scenarios'

describe('useScenariosStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.unstubAllGlobals()
  })

  it('initialises empty', () => {
    const store = useScenariosStore()
    expect(store.scenarios).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.hasScenarios).toBe(false)
  })

  it('fetchScenarios populates the list', async () => {
    const mockScenarios = [
      { id: 'outbound_campaign', name: 'Outbound Campaign', description: 'Test', category: 'gtm' },
    ]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ scenarios: mockScenarios }),
    }))

    const store = useScenariosStore()
    const result = await store.fetchScenarios()
    expect(result).toHaveLength(1)
    expect(store.scenarios[0].id).toBe('outbound_campaign')
    expect(store.hasScenarios).toBe(true)
    expect(store.loading).toBe(false)
  })

  it('fetchScenarios returns cached data without re-fetching', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ scenarios: [{ id: 'test' }] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const store = useScenariosStore()
    await store.fetchScenarios()
    await store.fetchScenarios()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('fetchScenarios with force bypasses cache', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ scenarios: [{ id: 'test' }] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const store = useScenariosStore()
    await store.fetchScenarios()
    await store.fetchScenarios(true)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('fetchScenarios handles errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))

    const store = useScenariosStore()
    const result = await store.fetchScenarios()
    expect(result).toEqual([])
    expect(store.error).toContain('500')
    expect(store.loading).toBe(false)
  })

  it('fetchScenarioById returns and caches a scenario', async () => {
    const detail = { id: 'pricing_simulation', name: 'Pricing', seed_text: 'Test pricing' }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(detail),
    }))

    const store = useScenariosStore()
    const result = await store.fetchScenarioById('pricing_simulation')
    expect(result.name).toBe('Pricing')
    expect(store.detailCache['pricing_simulation']).toBeDefined()
  })

  it('fetchScenarioById returns cached data on second call', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 'test', name: 'Test' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const store = useScenariosStore()
    await store.fetchScenarioById('test')
    const cached = await store.fetchScenarioById('test')
    expect(cached.name).toBe('Test')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('fetchScenarioById handles 404', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }))

    const store = useScenariosStore()
    const result = await store.fetchScenarioById('nonexistent')
    expect(result).toBeNull()
    expect(store.error).toContain('nonexistent')
  })

  it('clearCache resets all state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ scenarios: [{ id: 'x' }] }),
    }))

    const store = useScenariosStore()
    await store.fetchScenarios()
    store.clearCache()
    expect(store.scenarios).toEqual([])
    expect(store.detailCache).toEqual({})
    expect(store.error).toBeNull()
  })
})
