import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { API_BASE } from '../api/client'

export const useScenariosStore = defineStore('scenarios', () => {
  const scenarios = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Cache for individual scenario details (keyed by id)
  const detailCache = ref({})
  // ETag cache keyed by URL path
  const etags = ref({})

  const hasScenarios = computed(() => scenarios.value.length > 0)

  async function _fetchWithEtag(url, cacheKey) {
    const headers = {}
    if (etags.value[cacheKey]) {
      headers['If-None-Match'] = etags.value[cacheKey]
    }
    const res = await fetch(`${API_BASE}${url}`, { headers })
    if (res.status === 304) return null
    if (!res.ok) throw new Error(`Request failed: ${res.status}`)
    const etag = res.headers.get('ETag')
    if (etag) etags.value[cacheKey] = etag
    return res.json()
  }

  async function fetchScenarios(force = false) {
    if (scenarios.value.length > 0 && !force) return scenarios.value

    loading.value = true
    error.value = null
    try {
      const data = await _fetchWithEtag('/gtm/scenarios', 'scenarios')
      if (data) {
        scenarios.value = data.scenarios || []
      }
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
      const cacheKey = `scenario:${id}`
      const data = await _fetchWithEtag(`/gtm/scenarios/${id}`, cacheKey)
      if (data) {
        detailCache.value[id] = data
      }
      return detailCache.value[id] || null
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
    etags.value = {}
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
