import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { attributionApi } from '../api/attribution'

export const useAttributionStore = defineStore('attribution', () => {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const selectedModel = ref('linear')

  const hasData = computed(() => !!data.value)
  const models = computed(() => data.value?.model_labels ?? {})
  const channels = computed(() => data.value?.channels ?? [])
  const summary = computed(() => data.value?.summary ?? null)
  const insight = computed(() => data.value?.insight ?? null)

  async function fetchAnalysis(simulationId) {
    loading.value = true
    error.value = null
    try {
      const res = await attributionApi.getAnalysis(simulationId)
      if (res.data?.success) {
        data.value = res.data.data
      } else {
        throw new Error(res.data?.error || 'Failed to load attribution data')
      }
    } catch (e) {
      error.value = e.message || 'Network error'
    } finally {
      loading.value = false
    }
  }

  function setModel(modelId) {
    selectedModel.value = modelId
  }

  function reset() {
    data.value = null
    loading.value = false
    error.value = null
    selectedModel.value = 'linear'
  }

  return {
    data,
    loading,
    error,
    selectedModel,
    hasData,
    models,
    channels,
    summary,
    insight,
    fetchAnalysis,
    setModel,
    reset,
  }
})
