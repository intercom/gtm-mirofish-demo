import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useScenariosStore } from '../scenarios'

vi.mock('../../api/scenarios', () => ({
  scenariosApi: {
    list: vi.fn(),
    get: vi.fn(),
  },
}))

import { scenariosApi } from '../../api/scenarios'

const MOCK_SCENARIOS = [
  { id: 'outbound_campaign', name: 'Outbound Campaign Pre-Testing' },
  { id: 'signal_validation', name: 'Sales Signal Validation' },
]

const MOCK_DETAIL = {
  id: 'outbound_campaign',
  name: 'Outbound Campaign Pre-Testing',
  seed_text: 'Test seed text',
}

describe('scenarios store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initializes with empty state', () => {
    const store = useScenariosStore()
    expect(store.scenarios).toEqual([])
    expect(store.scenarioDetails).toEqual({})
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.scenarioCount).toBe(0)
  })

  it('fetches all scenarios', async () => {
    scenariosApi.list.mockResolvedValueOnce({ data: MOCK_SCENARIOS })
    const store = useScenariosStore()
    const result = await store.fetchAll()
    expect(scenariosApi.list).toHaveBeenCalled()
    expect(result).toEqual(MOCK_SCENARIOS)
    expect(store.scenarios).toEqual(MOCK_SCENARIOS)
    expect(store.scenarioCount).toBe(2)
    expect(store.loading).toBe(false)
  })

  it('returns cached scenarios on subsequent fetchAll', async () => {
    scenariosApi.list.mockResolvedValueOnce({ data: MOCK_SCENARIOS })
    const store = useScenariosStore()
    await store.fetchAll()
    await store.fetchAll()
    expect(scenariosApi.list).toHaveBeenCalledTimes(1)
  })

  it('fetches single scenario detail', async () => {
    scenariosApi.get.mockResolvedValueOnce({ data: MOCK_DETAIL })
    const store = useScenariosStore()
    const result = await store.fetchOne('outbound_campaign')
    expect(scenariosApi.get).toHaveBeenCalledWith('outbound_campaign')
    expect(result).toEqual(MOCK_DETAIL)
    expect(store.scenarioDetails.outbound_campaign).toEqual(MOCK_DETAIL)
  })

  it('returns cached detail on subsequent fetchOne', async () => {
    scenariosApi.get.mockResolvedValueOnce({ data: MOCK_DETAIL })
    const store = useScenariosStore()
    await store.fetchOne('outbound_campaign')
    await store.fetchOne('outbound_campaign')
    expect(scenariosApi.get).toHaveBeenCalledTimes(1)
  })

  it('getById returns detail if cached', async () => {
    scenariosApi.get.mockResolvedValueOnce({ data: MOCK_DETAIL })
    const store = useScenariosStore()
    await store.fetchOne('outbound_campaign')
    expect(store.getById('outbound_campaign')).toEqual(MOCK_DETAIL)
  })

  it('getById falls back to list entry', async () => {
    scenariosApi.list.mockResolvedValueOnce({ data: MOCK_SCENARIOS })
    const store = useScenariosStore()
    await store.fetchAll()
    expect(store.getById('signal_validation')).toEqual(MOCK_SCENARIOS[1])
  })

  it('getById returns null for unknown id', () => {
    const store = useScenariosStore()
    expect(store.getById('nonexistent')).toBeNull()
  })

  it('handles fetchAll errors', async () => {
    scenariosApi.list.mockRejectedValueOnce(new Error('Network error'))
    const store = useScenariosStore()
    const result = await store.fetchAll()
    expect(result).toEqual([])
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })

  it('handles fetchOne errors', async () => {
    scenariosApi.get.mockRejectedValueOnce(new Error('Not found'))
    const store = useScenariosStore()
    const result = await store.fetchOne('bad-id')
    expect(result).toBeNull()
    expect(store.error).toBe('Not found')
  })

  it('clears cache', async () => {
    scenariosApi.list.mockResolvedValueOnce({ data: MOCK_SCENARIOS })
    const store = useScenariosStore()
    await store.fetchAll()
    store.clearCache()
    expect(store.scenarios).toEqual([])
    expect(store.scenarioDetails).toEqual({})
  })
})
