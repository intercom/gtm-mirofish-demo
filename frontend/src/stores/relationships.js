import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { simulationApi } from '../api/simulation'

export const useRelationshipsStore = defineStore('relationships', () => {
  const agents = ref([])
  const relationships = ref([])
  const alliances = ref([])
  const conflicts = ref([])
  const isDemo = ref(false)
  const loading = ref(false)
  const error = ref(null)

  const hasData = computed(() => relationships.value.length > 0)

  const positiveRelationships = computed(() =>
    relationships.value.filter(r => r.affinity > 0.1),
  )

  const negativeRelationships = computed(() =>
    relationships.value.filter(r => r.affinity < -0.1),
  )

  async function fetchRelationships(simulationId) {
    if (!simulationId) return
    loading.value = true
    error.value = null

    try {
      const { data: res } = await simulationApi.getRelationships(simulationId)
      if (res.success) {
        agents.value = res.data.agents || []
        relationships.value = res.data.relationships || []
        alliances.value = res.data.alliances || []
        conflicts.value = res.data.conflicts || []
        isDemo.value = res.data.demo || false
      }
    } catch (e) {
      error.value = e.message || 'Failed to load relationships'
    } finally {
      loading.value = false
    }
  }

  function reset() {
    agents.value = []
    relationships.value = []
    alliances.value = []
    conflicts.value = []
    isDemo.value = false
    error.value = null
  }

  return {
    agents,
    relationships,
    alliances,
    conflicts,
    isDemo,
    loading,
    error,
    hasData,
    positiveRelationships,
    negativeRelationships,
    fetchRelationships,
    reset,
  }
})
