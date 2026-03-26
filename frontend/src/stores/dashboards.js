import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { dashboardsApi } from '../api/dashboards'

const STORAGE_KEY = 'mirofish_dashboards'

function loadStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function persist(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // Storage full or unavailable
  }
}

function makeDefaultDashboard() {
  return {
    id: 'default',
    name: 'GTM Overview',
    widgets: [],
    layout: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
}

export const useDashboardStore = defineStore('dashboards', () => {
  const dashboards = ref([])
  const activeDashboard = ref(null)
  const editMode = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // Snapshot of the active dashboard at last save/load — used for dirty tracking
  let savedSnapshot = null

  const widgetConfigs = computed(() =>
    activeDashboard.value?.widgets ?? [],
  )

  const layoutItems = computed(() =>
    activeDashboard.value?.layout ?? [],
  )

  const widgetCount = computed(() =>
    activeDashboard.value?.widgets?.length ?? 0,
  )

  const isDirty = computed(() => {
    if (!activeDashboard.value || !savedSnapshot) return false
    return JSON.stringify(activeDashboard.value) !== savedSnapshot
  })

  function snapshot() {
    savedSnapshot = activeDashboard.value
      ? JSON.stringify(activeDashboard.value)
      : null
  }

  async function fetchDashboards(force = false) {
    if (dashboards.value.length > 0 && !force) return dashboards.value

    loading.value = true
    error.value = null
    try {
      const res = await dashboardsApi.list()
      dashboards.value = res.data?.dashboards ?? res.data ?? []
      return dashboards.value
    } catch {
      // Backend not available — fall back to localStorage / default
      const stored = loadStored()
      dashboards.value = stored?.dashboards ?? [makeDefaultDashboard()]
      persist({ dashboards: dashboards.value })
      return dashboards.value
    } finally {
      loading.value = false
    }
  }

  async function fetchDashboard(id) {
    loading.value = true
    error.value = null
    try {
      const res = await dashboardsApi.get(id)
      activeDashboard.value = res.data
    } catch {
      // Fall back to local list
      activeDashboard.value =
        dashboards.value.find((d) => d.id === id) || makeDefaultDashboard()
    } finally {
      loading.value = false
      snapshot()
    }
    return activeDashboard.value
  }

  async function saveDashboard(config) {
    const dashboard = config ?? activeDashboard.value
    if (!dashboard) return null

    loading.value = true
    error.value = null
    dashboard.updatedAt = Date.now()

    try {
      const res = await dashboardsApi.save(dashboard)
      const saved = res.data ?? dashboard
      upsertLocal(saved)
      if (activeDashboard.value?.id === saved.id) {
        activeDashboard.value = saved
      }
      snapshot()
      return saved
    } catch {
      // Persist locally as fallback
      upsertLocal(dashboard)
      persist({ dashboards: dashboards.value })
      snapshot()
      return dashboard
    } finally {
      loading.value = false
    }
  }

  function createDashboard(name = 'Untitled Dashboard') {
    const dashboard = {
      id: `dashboard_${Date.now()}`,
      name,
      widgets: [],
      layout: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
    dashboards.value.push(dashboard)
    activeDashboard.value = dashboard
    snapshot()
    persist({ dashboards: dashboards.value })
    return dashboard
  }

  function renameDashboard(id, name) {
    const dash = dashboards.value.find((d) => d.id === id)
    if (!dash) return
    dash.name = name
    dash.updatedAt = Date.now()
    if (activeDashboard.value?.id === id) {
      activeDashboard.value.name = name
    }
    persist({ dashboards: dashboards.value })
  }

  async function deleteDashboard(id) {
    loading.value = true
    error.value = null
    try {
      await dashboardsApi.delete(id)
    } catch {
      // Continue with local removal even if backend fails
    } finally {
      dashboards.value = dashboards.value.filter((d) => d.id !== id)
      if (activeDashboard.value?.id === id) {
        activeDashboard.value = null
        savedSnapshot = null
      }
      persist({ dashboards: dashboards.value })
      loading.value = false
    }
  }

  async function duplicateDashboard(id) {
    const source = dashboards.value.find((d) => d.id === id)
    if (!source) return null

    loading.value = true
    error.value = null
    try {
      const res = await dashboardsApi.duplicate(id)
      const dup = res.data
      dashboards.value.push(dup)
      return dup
    } catch {
      // Local duplicate
      const dup = {
        ...JSON.parse(JSON.stringify(source)),
        id: `dashboard_${Date.now()}`,
        name: `${source.name} (copy)`,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      }
      dashboards.value.push(dup)
      persist({ dashboards: dashboards.value })
      return dup
    } finally {
      loading.value = false
    }
  }

  function setEditMode(val) {
    editMode.value = val
  }

  function addWidget(widgetConfig) {
    if (!activeDashboard.value) return
    const widget = {
      ...widgetConfig,
      id: widgetConfig.id || `widget_${Date.now()}`,
    }
    activeDashboard.value.widgets.push(widget)
    activeDashboard.value.layout.push({
      widgetId: widget.id,
      x: 0,
      y: 0,
      w: widgetConfig.w ?? 4,
      h: widgetConfig.h ?? 3,
    })
  }

  function removeWidget(widgetId) {
    if (!activeDashboard.value) return
    activeDashboard.value.widgets = activeDashboard.value.widgets.filter(
      (w) => w.id !== widgetId,
    )
    activeDashboard.value.layout = activeDashboard.value.layout.filter(
      (l) => l.widgetId !== widgetId,
    )
  }

  function updateWidgetConfig(widgetId, config) {
    if (!activeDashboard.value) return
    const widget = activeDashboard.value.widgets.find((w) => w.id === widgetId)
    if (widget) Object.assign(widget, config)
  }

  function updateLayout(items) {
    if (!activeDashboard.value) return
    activeDashboard.value.layout = items
  }

  function upsertLocal(dashboard) {
    const idx = dashboards.value.findIndex((d) => d.id === dashboard.id)
    if (idx !== -1) {
      dashboards.value[idx] = dashboard
    } else {
      dashboards.value.push(dashboard)
    }
  }

  return {
    // State
    dashboards,
    activeDashboard,
    editMode,
    loading,
    error,
    // Getters
    widgetConfigs,
    layoutItems,
    widgetCount,
    isDirty,
    // Actions
    fetchDashboards,
    fetchDashboard,
    saveDashboard,
    createDashboard,
    renameDashboard,
    deleteDashboard,
    duplicateDashboard,
    setEditMode,
    addWidget,
    removeWidget,
    updateWidgetConfig,
    updateLayout,
  }
})
