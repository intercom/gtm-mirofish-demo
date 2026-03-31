import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/activity', () => ({
  activityApi: {
    getRecent: vi.fn(),
  },
}))

import { useActivityStore } from '../activity'
import { activityApi } from '../../api/activity'

describe('useActivityStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initialises with empty state', () => {
    const store = useActivityStore()
    expect(store.items).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.filters).toEqual({ types: [], limit: 20 })
  })

  // --- Computed ---

  it('hasItems is false when empty', () => {
    const store = useActivityStore()
    expect(store.hasItems).toBe(false)
  })

  it('hasItems is true when items exist', () => {
    const store = useActivityStore()
    store.items = [{ id: '1' }]
    expect(store.hasItems).toBe(true)
  })

  it('criticalCount filters by severity critical', () => {
    const store = useActivityStore()
    store.items = [
      { id: '1', severity: 'critical' },
      { id: '2', severity: 'warning' },
      { id: '3', severity: 'critical' },
      { id: '4', severity: 'info' },
    ]
    expect(store.criticalCount).toBe(2)
  })

  it('criticalCount is 0 when no critical items', () => {
    const store = useActivityStore()
    store.items = [{ id: '1', severity: 'info' }]
    expect(store.criticalCount).toBe(0)
  })

  it('warningCount filters by severity warning', () => {
    const store = useActivityStore()
    store.items = [
      { id: '1', severity: 'warning' },
      { id: '2', severity: 'critical' },
      { id: '3', severity: 'warning' },
    ]
    expect(store.warningCount).toBe(2)
  })

  it('warningCount is 0 when no warning items', () => {
    const store = useActivityStore()
    store.items = [{ id: '1', severity: 'info' }]
    expect(store.warningCount).toBe(0)
  })

  // --- setFilters ---

  it('setFilters merges new filter values', () => {
    const store = useActivityStore()
    store.setFilters({ limit: 50 })
    expect(store.filters).toEqual({ types: [], limit: 50 })
  })

  it('setFilters preserves existing values not overwritten', () => {
    const store = useActivityStore()
    store.setFilters({ types: ['error', 'warning'] })
    expect(store.filters.limit).toBe(20)
    expect(store.filters.types).toEqual(['error', 'warning'])
  })

  // --- clear ---

  it('clear resets items and error', () => {
    const store = useActivityStore()
    store.items = [{ id: '1' }]
    store.error = 'some error'

    store.clear()

    expect(store.items).toEqual([])
    expect(store.error).toBeNull()
  })

  // --- fetchRecent ---

  it('fetchRecent populates items on success', async () => {
    const mockItems = [
      { id: '1', severity: 'info', message: 'Action 1' },
      { id: '2', severity: 'critical', message: 'Action 2' },
    ]
    activityApi.getRecent.mockResolvedValue({
      data: { items: mockItems },
    })

    const store = useActivityStore()
    const result = await store.fetchRecent()

    expect(result).toEqual(mockItems)
    expect(store.items).toEqual(mockItems)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRecent handles nested data.data response', async () => {
    const mockItems = [{ id: '1' }]
    activityApi.getRecent.mockResolvedValue({
      data: { data: { items: mockItems } },
    })

    const store = useActivityStore()
    const result = await store.fetchRecent()

    expect(result).toEqual(mockItems)
    expect(store.items).toEqual(mockItems)
  })

  it('fetchRecent sets error and returns empty array on failure', async () => {
    activityApi.getRecent.mockRejectedValue(new Error('Server error'))

    const store = useActivityStore()
    const result = await store.fetchRecent()

    expect(result).toEqual([])
    expect(store.error).toBe('Server error')
    expect(store.loading).toBe(false)
  })

  it('fetchRecent uses default filters for params', async () => {
    activityApi.getRecent.mockResolvedValue({ data: { items: [] } })

    const store = useActivityStore()
    await store.fetchRecent()

    expect(activityApi.getRecent).toHaveBeenCalledWith({ limit: 20 })
  })

  it('fetchRecent uses opts to override filters', async () => {
    activityApi.getRecent.mockResolvedValue({ data: { items: [] } })

    const store = useActivityStore()
    await store.fetchRecent({ limit: 5, types: ['error'] })

    expect(activityApi.getRecent).toHaveBeenCalledWith({
      limit: 5,
      types: 'error',
    })
  })

  it('fetchRecent joins multiple types with commas', async () => {
    activityApi.getRecent.mockResolvedValue({ data: { items: [] } })

    const store = useActivityStore()
    await store.fetchRecent({ types: ['error', 'warning'] })

    expect(activityApi.getRecent).toHaveBeenCalledWith(
      expect.objectContaining({ types: 'error,warning' }),
    )
  })

  it('fetchRecent includes since param when provided', async () => {
    activityApi.getRecent.mockResolvedValue({ data: { items: [] } })

    const store = useActivityStore()
    await store.fetchRecent({ since: '2026-01-01' })

    expect(activityApi.getRecent).toHaveBeenCalledWith(
      expect.objectContaining({ since: '2026-01-01' }),
    )
  })

  it('fetchRecent uses store filters when no types in opts', async () => {
    activityApi.getRecent.mockResolvedValue({ data: { items: [] } })

    const store = useActivityStore()
    store.setFilters({ types: ['audit'], limit: 10 })
    await store.fetchRecent()

    expect(activityApi.getRecent).toHaveBeenCalledWith({
      limit: 10,
      types: 'audit',
    })
  })

  it('fetchRecent defaults error message when e.message is empty', async () => {
    activityApi.getRecent.mockRejectedValue({ message: '' })

    const store = useActivityStore()
    await store.fetchRecent()

    expect(store.error).toBe('Failed to fetch activity feed')
  })
})
