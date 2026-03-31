import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { aggregationApi } from '../api/aggregation'

export const useAggregationStore = defineStore('aggregation', () => {
  const loading = ref(false)
  const error = ref(null)

  // Selected simulation IDs for comparison
  const selectedIds = ref([])

  // Cached results keyed by mode
  const results = ref({})

  const hasSelection = computed(() => selectedIds.value.length > 0)
  const selectionCount = computed(() => selectedIds.value.length)

  function selectSimulations(ids) {
    selectedIds.value = [...ids]
    results.value = {}
    error.value = null
  }

  function toggleSimulation(id) {
    const idx = selectedIds.value.indexOf(id)
    if (idx === -1) {
      selectedIds.value.push(id)
    } else {
      selectedIds.value.splice(idx, 1)
    }
    results.value = {}
  }

  async function fetchAggregation(mode = 'metrics', params = {}) {
    if (selectedIds.value.length === 0) return null

    loading.value = true
    error.value = null
    try {
      const res = await aggregationApi.aggregate(selectedIds.value, mode, params)
      const data = res.data?.data ?? res.data
      results.value[mode] = data
      return data
    } catch (e) {
      error.value = e.message || 'Aggregation failed'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchAll() {
    return fetchAggregation('all')
  }

  function clearSelection() {
    selectedIds.value = []
    results.value = {}
    error.value = null
  }

  return {
    loading,
    error,
    selectedIds,
    results,
    hasSelection,
    selectionCount,
    selectSimulations,
    toggleSimulation,
    fetchAggregation,
    fetchAll,
    clearSelection,
  }
})
