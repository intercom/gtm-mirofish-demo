import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { activityApi } from '../api/activity'

export const useActivityStore = defineStore('activity', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const filters = ref({ types: [], limit: 20 })

  const hasItems = computed(() => items.value.length > 0)

  const criticalCount = computed(
    () => items.value.filter((i) => i.severity === 'critical').length,
  )

  const warningCount = computed(
    () => items.value.filter((i) => i.severity === 'warning').length,
  )

  async function fetchRecent(opts = {}) {
    loading.value = true
    error.value = null
    try {
      const params = {
        limit: opts.limit ?? filters.value.limit,
      }
      const types = opts.types ?? filters.value.types
      if (types.length) params.types = types.join(',')
      if (opts.since) params.since = opts.since

      const res = await activityApi.getRecent(params)
      const data = res.data?.data ?? res.data
      items.value = data.items || []
      return items.value
    } catch (e) {
      error.value = e.message || 'Failed to fetch activity feed'
      return []
    } finally {
      loading.value = false
    }
  }

  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function clear() {
    items.value = []
    error.value = null
  }

  return {
    items,
    loading,
    error,
    filters,
    hasItems,
    criticalCount,
    warningCount,
    fetchRecent,
    setFilters,
    clear,
  }
})
