import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { simulationApi } from '@/api/simulation'

export const useCoalitionStore = defineStore('coalition', () => {
  const coalitions = ref([])
  const evolution = ref([])
  const polarization = ref([])
  const swingAgents = ref([])
  const loading = ref(false)
  const error = ref(null)

  const coalitionCount = computed(() => coalitions.value.length)
  const latestPolarization = computed(() => {
    if (!polarization.value.length) return 0
    return polarization.value[polarization.value.length - 1].polarization_index
  })

  async function fetchCoalitions(simulationId) {
    loading.value = true
    error.value = null
    try {
      const { data } = await simulationApi.getCoalitions(simulationId)
      if (data.success) {
        coalitions.value = data.data.coalitions
      }
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchEvolution(simulationId) {
    try {
      const { data } = await simulationApi.getCoalitionEvolution(simulationId)
      if (data.success) {
        evolution.value = data.data.evolution
      }
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchPolarization(simulationId) {
    try {
      const { data } = await simulationApi.getPolarization(simulationId)
      if (data.success) {
        polarization.value = data.data.timeline
      }
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchSwingAgents(simulationId) {
    try {
      const { data } = await simulationApi.getSwingAgents(simulationId)
      if (data.success) {
        swingAgents.value = data.data.swing_agents
      }
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchAll(simulationId) {
    loading.value = true
    error.value = null
    try {
      await Promise.all([
        fetchCoalitions(simulationId),
        fetchEvolution(simulationId),
        fetchPolarization(simulationId),
        fetchSwingAgents(simulationId),
      ])
    } finally {
      loading.value = false
    }
  }

  function reset() {
    coalitions.value = []
    evolution.value = []
    polarization.value = []
    swingAgents.value = []
    loading.value = false
    error.value = null
  }

  return {
    coalitions,
    evolution,
    polarization,
    swingAgents,
    loading,
    error,
    coalitionCount,
    latestPolarization,
    fetchCoalitions,
    fetchEvolution,
    fetchPolarization,
    fetchSwingAgents,
    fetchAll,
    reset,
  }
})
