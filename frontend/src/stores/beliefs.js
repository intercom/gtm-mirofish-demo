import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { beliefsApi } from '../api/beliefs'

export const useBeliefsStore = defineStore('beliefs', () => {
  const rounds = ref([])
  const dimensions = ref([])
  const mode = ref(null) // 'keyword' | 'llm' | 'demo'
  const loading = ref(false)
  const error = ref(null)

  const hasData = computed(() => rounds.value.length > 0)

  const latestRound = computed(() =>
    rounds.value.length ? rounds.value[rounds.value.length - 1] : null,
  )

  async function fetchDimensions() {
    try {
      const res = await beliefsApi.getDimensions()
      dimensions.value = res.data.dimensions
    } catch (e) {
      dimensions.value = fallbackDimensions()
    }
  }

  async function extractBeliefs(simulationId, actions, useLlm = false) {
    loading.value = true
    error.value = null
    try {
      const res = await beliefsApi.extract(simulationId, actions, useLlm)
      rounds.value = res.data.rounds
      mode.value = res.data.mode
    } catch (e) {
      error.value = e.message || 'Failed to extract beliefs'
    } finally {
      loading.value = false
    }
  }

  async function fetchDemo(numRounds = 10) {
    loading.value = true
    error.value = null
    try {
      const res = await beliefsApi.demo(numRounds)
      rounds.value = res.data.rounds
      mode.value = 'demo'
    } catch (e) {
      error.value = e.message || 'Failed to fetch demo beliefs'
    } finally {
      loading.value = false
    }
  }

  function reset() {
    rounds.value = []
    mode.value = null
    loading.value = false
    error.value = null
  }

  return {
    rounds,
    dimensions,
    mode,
    loading,
    error,
    hasData,
    latestRound,
    fetchDimensions,
    extractBeliefs,
    fetchDemo,
    reset,
  }
})

function fallbackDimensions() {
  return [
    { key: 'product_quality', label: 'Product Quality', color: '#2068FF' },
    { key: 'pricing', label: 'Pricing Perception', color: '#ff5600' },
    { key: 'brand_trust', label: 'Brand Trust', color: '#009900' },
    { key: 'competitive_position', label: 'Competitive Position', color: '#AA00FF' },
    { key: 'adoption_intent', label: 'Adoption Intent', color: '#E67E00' },
  ]
}
