import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { insightsApi } from '../api/insights'

export const useInsightsStore = defineStore('insights', () => {
  const insights = ref([])
  const loading = ref(false)
  const error = ref(null)
  const dataType = ref(null)
  const mode = ref(null)

  const hasInsights = computed(() => insights.value.length > 0)

  async function fetchInsights(params = {}) {
    loading.value = true
    error.value = null
    try {
      const { data: res } = await insightsApi.get(params)
      if (res.success) {
        insights.value = res.data.insights
        dataType.value = res.data.data_type
        mode.value = res.data.mode
      } else {
        error.value = res.error || 'Failed to fetch insights'
      }
    } catch (e) {
      error.value = e.message || 'Network error'
    } finally {
      loading.value = false
    }
  }

  async function generateInsights(payload) {
    loading.value = true
    error.value = null
    try {
      const { data: res } = await insightsApi.generate(payload)
      if (res.success) {
        insights.value = res.data.insights
        dataType.value = res.data.data_type
        mode.value = res.data.mode
      } else {
        error.value = res.error || 'Failed to generate insights'
      }
    } catch (e) {
      error.value = e.message || 'Network error'
    } finally {
      loading.value = false
    }
  }

  function clear() {
    insights.value = []
    error.value = null
    dataType.value = null
    mode.value = null
  }

  return {
    insights,
    loading,
    error,
    dataType,
    mode,
    hasInsights,
    fetchInsights,
    generateInsights,
    clear,
  }
})
