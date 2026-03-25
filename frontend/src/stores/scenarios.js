import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { API_BASE } from '../api/client'

const STORAGE_KEY = 'mirofish_scenarios'
const DETAIL_STORAGE_KEY = 'mirofish_scenario_details'

function loadCached(key) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function saveCache(key, data) {
  try {
    localStorage.setItem(key, JSON.stringify(data))
  } catch {
    // Storage full — silently ignore
  }
}

export const useScenariosStore = defineStore('scenarios', () => {
  const scenarios = ref(loadCached(STORAGE_KEY) || [])
  const loading = ref(false)
  const error = ref(null)
  const detailCache = ref(loadCached(DETAIL_STORAGE_KEY) || {})

  const hasScenarios = computed(() => scenarios.value.length > 0)

  // Persist scenarios list and detail cache on change
  watch(scenarios, (val) => saveCache(STORAGE_KEY, val), { deep: true })
  watch(detailCache, (val) => saveCache(DETAIL_STORAGE_KEY, val), { deep: true })

  async function fetchScenarios(force = false) {
    if (scenarios.value.length > 0 && !force) return scenarios.value

    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/gtm/scenarios`)
      if (!res.ok) throw new Error(`Failed to fetch scenarios: ${res.status}`)
      const data = await res.json()
      scenarios.value = data.scenarios || []
      return scenarios.value
    } catch (e) {
      error.value = e.message
      // Offline fallback: return cached data if available
      if (scenarios.value.length > 0) return scenarios.value
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchScenarioById(id, force = false) {
    if (detailCache.value[id] && !force) return detailCache.value[id]

    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/gtm/scenarios/${id}`)
      if (!res.ok) throw new Error(`Scenario not found: ${id}`)
      const data = await res.json()
      detailCache.value[id] = data
      return data
    } catch (e) {
      error.value = e.message
      // Offline fallback: return cached detail if available
      if (detailCache.value[id]) return detailCache.value[id]
      return null
    } finally {
      loading.value = false
    }
  }

  function clearCache() {
    scenarios.value = []
    detailCache.value = {}
    error.value = null
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(DETAIL_STORAGE_KEY)
  }

  return {
    scenarios,
    loading,
    error,
    detailCache,
    hasScenarios,
    fetchScenarios,
    fetchScenarioById,
    clearCache,
  }
})
