import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish_dashboards'

function loadDashboards() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveDashboards(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

export const useDashboardStore = defineStore('dashboards', () => {
  const dashboards = ref(loadDashboards())
  const activeDashboardId = ref(dashboards.value[0]?.id ?? null)

  const activeDashboard = computed(() =>
    dashboards.value.find((d) => d.id === activeDashboardId.value) ?? null,
  )

  function createDashboard(name = 'Untitled Dashboard') {
    const dashboard = {
      id: `dash-${Date.now()}`,
      name,
      layout: [],
      createdAt: new Date().toISOString(),
    }
    dashboards.value.push(dashboard)
    activeDashboardId.value = dashboard.id
    saveDashboards(dashboards.value)
    return dashboard
  }

  function updateLayout(id, layout) {
    const dash = dashboards.value.find((d) => d.id === id)
    if (dash) {
      dash.layout = layout
      saveDashboards(dashboards.value)
    }
  }

  function renameDashboard(id, name) {
    const dash = dashboards.value.find((d) => d.id === id)
    if (dash) {
      dash.name = name
      saveDashboards(dashboards.value)
    }
  }

  function deleteDashboard(id) {
    dashboards.value = dashboards.value.filter((d) => d.id !== id)
    if (activeDashboardId.value === id) {
      activeDashboardId.value = dashboards.value[0]?.id ?? null
    }
    saveDashboards(dashboards.value)
  }

  function removeWidget(dashboardId, widgetId) {
    const dash = dashboards.value.find((d) => d.id === dashboardId)
    if (dash) {
      dash.layout = dash.layout.filter((item) => item.i !== widgetId)
      saveDashboards(dashboards.value)
    }
  }

  return {
    dashboards,
    activeDashboardId,
    activeDashboard,
    createDashboard,
    updateLayout,
    renameDashboard,
    deleteDashboard,
    removeWidget,
  }
})
