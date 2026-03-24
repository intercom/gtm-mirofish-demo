import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { API_BASE } from '../api/client'

export const useScenariosStore = defineStore('scenarios', () => {
  const scenarios = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Cache for individual scenario details (keyed by id)
  const detailCache = ref({})

  const hasScenarios = computed(() => scenarios.value.length > 0)

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
      return null
    } finally {
      loading.value = false
    }
  }

  function clearCache() {
    scenarios.value = []
    detailCache.value = {}
    error.value = null
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
