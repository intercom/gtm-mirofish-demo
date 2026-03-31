import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/dashboards', () => ({
  dashboardsApi: {
    list: vi.fn(),
    get: vi.fn(),
    save: vi.fn(),
    delete: vi.fn(),
    duplicate: vi.fn(),
  },
}))

import { useDashboardStore } from '../dashboards'
import { dashboardsApi } from '../../api/dashboards'

describe('useDashboardStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initialises with empty state', () => {
    const store = useDashboardStore()
    expect(store.dashboards).toEqual([])
    expect(store.activeDashboard).toBeNull()
    expect(store.editMode).toBe(false)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- Computed ---

  it('widgetConfigs returns empty array when no active dashboard', () => {
    const store = useDashboardStore()
    expect(store.widgetConfigs).toEqual([])
  })

  it('widgetConfigs returns widgets of active dashboard', () => {
    const store = useDashboardStore()
    store.activeDashboard = { widgets: [{ id: 'w1' }], layout: [] }
    expect(store.widgetConfigs).toEqual([{ id: 'w1' }])
  })

  it('layoutItems returns empty array when no active dashboard', () => {
    const store = useDashboardStore()
    expect(store.layoutItems).toEqual([])
  })

  it('layoutItems returns layout of active dashboard', () => {
    const store = useDashboardStore()
    store.activeDashboard = { widgets: [], layout: [{ i: 'w1', x: 0, y: 0 }] }
    expect(store.layoutItems).toEqual([{ i: 'w1', x: 0, y: 0 }])
  })

  it('widgetCount is 0 when no active dashboard', () => {
    const store = useDashboardStore()
    expect(store.widgetCount).toBe(0)
  })

  it('widgetCount returns layout length', () => {
    const store = useDashboardStore()
    store.activeDashboard = { widgets: [], layout: [{ i: 'w1' }, { i: 'w2' }] }
    expect(store.widgetCount).toBe(2)
  })

  it('isDirty is false initially', () => {
    const store = useDashboardStore()
    expect(store.isDirty).toBe(false)
  })

  it('isDirty detects changes after createDashboard', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    expect(store.isDirty).toBe(false)

    store.activeDashboard.name = 'Changed'
    expect(store.isDirty).toBe(true)
  })

  // --- createDashboard ---

  it('createDashboard creates with generated id and adds to list', () => {
    const store = useDashboardStore()
    const dash = store.createDashboard('My Dashboard')

    expect(dash.id).toMatch(/^dashboard_/)
    expect(dash.name).toBe('My Dashboard')
    expect(dash.widgets).toEqual([])
    expect(dash.layout).toEqual([])
    expect(store.dashboards).toHaveLength(1)
    expect(store.activeDashboard).toEqual(dash)
  })

  it('createDashboard uses default name when none provided', () => {
    const store = useDashboardStore()
    const dash = store.createDashboard()
    expect(dash.name).toBe('Untitled Dashboard')
  })

  it('createDashboard persists to localStorage', () => {
    const store = useDashboardStore()
    store.createDashboard('Stored')

    const stored = JSON.parse(localStorage.getItem('mirofish_dashboards'))
    expect(stored.dashboards).toHaveLength(1)
    expect(stored.dashboards[0].name).toBe('Stored')
  })

  // --- renameDashboard ---

  it('renameDashboard updates name and updatedAt', () => {
    const store = useDashboardStore()
    const dash = store.createDashboard('Original')
    const originalUpdatedAt = dash.updatedAt

    // Small delay to ensure timestamp differs
    vi.spyOn(Date, 'now').mockReturnValue(originalUpdatedAt + 1000)
    store.renameDashboard(dash.id, 'Renamed')

    expect(store.dashboards[0].name).toBe('Renamed')
    expect(store.dashboards[0].updatedAt).toBe(originalUpdatedAt + 1000)
    vi.restoreAllMocks()
  })

  it('renameDashboard updates active dashboard name if matching', () => {
    const store = useDashboardStore()
    const dash = store.createDashboard('Original')
    store.renameDashboard(dash.id, 'Renamed')

    expect(store.activeDashboard.name).toBe('Renamed')
  })

  it('renameDashboard is no-op for unknown id', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    store.renameDashboard('nonexistent', 'Renamed')

    expect(store.dashboards[0].name).toBe('Test')
  })

  // --- setEditMode ---

  it('setEditMode toggles edit mode', () => {
    const store = useDashboardStore()
    expect(store.editMode).toBe(false)

    store.setEditMode(true)
    expect(store.editMode).toBe(true)

    store.setEditMode(false)
    expect(store.editMode).toBe(false)
  })

  // --- addWidget ---

  it('addWidget adds to active dashboard layout', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    store.addWidget({ id: 'w1', type: 'chart', config: { metric: 'revenue' } })

    expect(store.activeDashboard.layout).toHaveLength(1)
    expect(store.activeDashboard.layout[0].i).toBe('w1')
    expect(store.activeDashboard.layout[0].type).toBe('chart')
    expect(store.activeDashboard.layout[0].config).toEqual({ metric: 'revenue' })
    expect(store.activeDashboard.layout[0].x).toBe(0)
    expect(store.activeDashboard.layout[0].y).toBe(0)
    expect(store.activeDashboard.layout[0].w).toBe(4)
    expect(store.activeDashboard.layout[0].h).toBe(3)
  })

  it('addWidget stacks new widgets below existing ones', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    store.addWidget({ id: 'w1', type: 'chart', h: 3 })
    store.addWidget({ id: 'w2', type: 'table' })

    expect(store.activeDashboard.layout[1].y).toBe(3)
  })

  it('addWidget is no-op when no active dashboard', () => {
    const store = useDashboardStore()
    store.addWidget({ id: 'w1', type: 'chart' })
    expect(store.activeDashboard).toBeNull()
  })

  it('addWidget generates id when not provided', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    store.addWidget({ type: 'chart' })

    expect(store.activeDashboard.layout[0].i).toMatch(/^widget_/)
  })

  // --- removeWidget ---

  it('removeWidget filters out by widget id', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    store.addWidget({ id: 'w1', type: 'chart' })
    store.addWidget({ id: 'w2', type: 'table' })

    store.removeWidget('w1')

    expect(store.activeDashboard.layout).toHaveLength(1)
    expect(store.activeDashboard.layout[0].i).toBe('w2')
  })

  it('removeWidget is no-op when no active dashboard', () => {
    const store = useDashboardStore()
    store.removeWidget('w1')
    expect(store.activeDashboard).toBeNull()
  })

  // --- updateWidgetConfig ---

  it('updateWidgetConfig merges config into matching widget', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    store.addWidget({ id: 'w1', type: 'chart', w: 4, h: 3 })

    store.updateWidgetConfig('w1', { w: 8 })

    expect(store.activeDashboard.layout[0].w).toBe(8)
    expect(store.activeDashboard.layout[0].h).toBe(3)
  })

  it('updateWidgetConfig is no-op for unknown widget id', () => {
    const store = useDashboardStore()
    store.createDashboard('Test')
    store.addWidget({ id: 'w1', type: 'chart' })

    store.updateWidgetConfig('w-unknown', { w: 12 })

    expect(store.activeDashboard.layout[0].w).toBe(4)
  })

  it('updateWidgetConfig is no-op when no active dashboard', () => {
    const store = useDashboardStore()
    store.updateWidgetConfig('w1', { w: 8 })
    expect(store.activeDashboard).toBeNull()
  })

  // --- fetchDashboards ---

  it('fetchDashboards returns cached if not forced', async () => {
    const store = useDashboardStore()
    store.dashboards = [{ id: 'd1', name: 'Cached' }]

    const result = await store.fetchDashboards()

    expect(dashboardsApi.list).not.toHaveBeenCalled()
    expect(result).toEqual([{ id: 'd1', name: 'Cached' }])
  })

  it('fetchDashboards fetches from API when empty', async () => {
    const mockDashboards = [{ id: 'd1', name: 'From API' }]
    dashboardsApi.list.mockResolvedValue({
      data: { dashboards: mockDashboards },
    })

    const store = useDashboardStore()
    const result = await store.fetchDashboards()

    expect(dashboardsApi.list).toHaveBeenCalled()
    expect(result).toEqual(mockDashboards)
    expect(store.dashboards).toEqual(mockDashboards)
    expect(store.loading).toBe(false)
  })

  it('fetchDashboards with force bypasses cache', async () => {
    const mockDashboards = [{ id: 'd1', name: 'Fresh' }]
    dashboardsApi.list.mockResolvedValue({
      data: { dashboards: mockDashboards },
    })

    const store = useDashboardStore()
    store.dashboards = [{ id: 'old', name: 'Stale' }]
    const result = await store.fetchDashboards(true)

    expect(dashboardsApi.list).toHaveBeenCalled()
    expect(result).toEqual(mockDashboards)
  })

  it('fetchDashboards falls back to localStorage on API error', async () => {
    dashboardsApi.list.mockRejectedValue(new Error('Server down'))
    localStorage.setItem(
      'mirofish_dashboards',
      JSON.stringify({ dashboards: [{ id: 'stored', name: 'Stored' }] }),
    )

    const store = useDashboardStore()
    const result = await store.fetchDashboards()

    expect(result).toEqual([{ id: 'stored', name: 'Stored' }])
    expect(store.loading).toBe(false)
  })

  it('fetchDashboards creates default dashboard when no stored data', async () => {
    dashboardsApi.list.mockRejectedValue(new Error('Server down'))

    const store = useDashboardStore()
    const result = await store.fetchDashboards()

    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('default')
    expect(result[0].name).toBe('GTM Overview')
  })

  // --- deleteDashboard ---

  it('deleteDashboard removes from list and clears active if matching', async () => {
    dashboardsApi.delete.mockResolvedValue({})

    const store = useDashboardStore()
    store.createDashboard('To Delete')
    const id = store.dashboards[0].id

    await store.deleteDashboard(id)

    expect(store.dashboards).toHaveLength(0)
    expect(store.activeDashboard).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('deleteDashboard does not clear active if ids differ', async () => {
    dashboardsApi.delete.mockResolvedValue({})

    const store = useDashboardStore()
    // Manually set up two dashboards with distinct ids to avoid Date.now() collisions
    const dash1 = { id: 'dash-keep', name: 'Keep Active', widgets: [], layout: [], createdAt: 1, updatedAt: 1 }
    const dash2 = { id: 'dash-delete', name: 'Delete Me', widgets: [], layout: [], createdAt: 2, updatedAt: 2 }
    store.dashboards = [dash1, dash2]
    store.activeDashboard = dash1

    await store.deleteDashboard('dash-delete')

    expect(store.activeDashboard).toEqual(dash1)
    expect(store.dashboards).toHaveLength(1)
    expect(store.dashboards[0].id).toBe('dash-keep')
  })

  it('deleteDashboard removes locally even if API fails', async () => {
    dashboardsApi.delete.mockRejectedValue(new Error('Server error'))

    const store = useDashboardStore()
    store.createDashboard('Will be removed')
    const id = store.dashboards[0].id

    await store.deleteDashboard(id)

    expect(store.dashboards).toHaveLength(0)
  })

  it('deleteDashboard persists to localStorage', async () => {
    dashboardsApi.delete.mockResolvedValue({})

    const store = useDashboardStore()
    // Use distinct ids to avoid Date.now() collisions
    const dash1 = { id: 'dash-1', name: 'Dashboard 1', widgets: [], layout: [], createdAt: 1, updatedAt: 1 }
    const dash2 = { id: 'dash-2', name: 'Dashboard 2', widgets: [], layout: [], createdAt: 2, updatedAt: 2 }
    store.dashboards = [dash1, dash2]

    await store.deleteDashboard('dash-1')

    const stored = JSON.parse(localStorage.getItem('mirofish_dashboards'))
    expect(stored.dashboards).toHaveLength(1)
    expect(stored.dashboards[0].id).toBe('dash-2')
  })
})
