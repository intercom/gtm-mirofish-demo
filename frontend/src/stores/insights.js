import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { insightsApi } from '../api/insights'
import { listInsights, refreshInsights, pinInsight, dismissInsight } from '../api'

export const useInsightsStore = defineStore('insights', () => {
  const insights = ref([])
  const loading = ref(false)
  const error = ref(null)
  const dataType = ref(null)
  const mode = ref(null)
  const activeCategory = ref(null)

  const hasInsights = computed(() => insights.value.length > 0)

  const categories = computed(() => {
    const cats = new Set(insights.value.map(i => i.category))
    return Array.from(cats).sort()
  })

  const filteredInsights = computed(() => {
    if (!activeCategory.value) return insights.value
    return insights.value.filter(i => i.category === activeCategory.value)
  })

  const pinnedCount = computed(() => insights.value.filter(i => i.pinned).length)

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

  async function fetch(category) {
    loading.value = true
    error.value = null
    try {
      const res = await listInsights(category || undefined)
      insights.value = res.data
    } catch (e) {
      error.value = e.message
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

  async function refresh() {
    loading.value = true
    error.value = null
    try {
      const res = await refreshInsights()
      insights.value = res.data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function togglePin(insightId) {
    try {
      const res = await pinInsight(insightId)
      const idx = insights.value.findIndex(i => i.id === insightId)
      if (idx !== -1) insights.value[idx] = res.data
    } catch (e) {
      error.value = e.message
    }
  }

  async function dismiss(insightId) {
    try {
      await dismissInsight(insightId)
      insights.value = insights.value.filter(i => i.id !== insightId)
    } catch (e) {
      error.value = e.message
    }
  }

  function setCategory(category) {
    activeCategory.value = category
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
    activeCategory,
    categories,
    filteredInsights,
    pinnedCount,
    fetchInsights,
    generateInsights,
    clear,
    fetch,
    refresh,
    togglePin,
    dismiss,
    setCategory,
  }
})
