import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { scenariosApi } from '../api/scenarios'

export const useScenariosStore = defineStore('scenarios', () => {
  const scenarios = ref([])
  const scenarioDetails = ref({})
  const loading = ref(false)
  const error = ref(null)

  const scenarioCount = computed(() => scenarios.value.length)

  function getById(id) {
    return scenarioDetails.value[id] || scenarios.value.find((s) => s.id === id) || null
  }

  async function fetchAll() {
    if (scenarios.value.length) return scenarios.value
    loading.value = true
    error.value = null
    try {
      const { data } = await scenariosApi.list()
      scenarios.value = data
      return data
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    if (scenarioDetails.value[id]) return scenarioDetails.value[id]
    loading.value = true
    error.value = null
    try {
      const { data } = await scenariosApi.get(id)
      scenarioDetails.value[id] = data
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
    scenarioDetails.value = {}
  }

  return {
    scenarios,
    scenarioDetails,
    loading,
    error,
    scenarioCount,
    getById,
    fetchAll,
    fetchOne,
    clearCache,
  }
})
