import { ref, computed } from 'vue'
import { comparisonApi } from '../api/comparison'

export function useComparisonData() {
  const availableRuns = ref([])
  const selectedRunIds = ref([])
  const comparisonData = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const hasSelection = computed(() => selectedRunIds.value.length >= 2)

  async function fetchRuns() {
    try {
      const { data } = await comparisonApi.listRuns()
      availableRuns.value = data.data.runs
      if (selectedRunIds.value.length === 0 && availableRuns.value.length >= 2) {
        selectedRunIds.value = availableRuns.value.slice(0, 2).map(r => r.id)
      }
    } catch (e) {
      error.value = e.message || 'Failed to load runs'
    }
  }

  async function fetchComparison(metric) {
    if (!hasSelection.value) return
    loading.value = true
    error.value = null
    try {
      const { data } = await comparisonApi.getData(selectedRunIds.value, metric)
      comparisonData.value = data.data
    } catch (e) {
      error.value = e.message || 'Failed to load comparison data'
    } finally {
      loading.value = false
    }
  }

  function toggleRun(runId) {
    const idx = selectedRunIds.value.indexOf(runId)
    if (idx >= 0) {
      selectedRunIds.value.splice(idx, 1)
    } else if (selectedRunIds.value.length < 5) {
      selectedRunIds.value.push(runId)
    }
  }

  return {
    availableRuns,
    selectedRunIds,
    comparisonData,
    loading,
    error,
    hasSelection,
    fetchRuns,
    fetchComparison,
    toggleRun,
  }
}
