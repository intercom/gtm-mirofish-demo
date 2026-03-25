import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { agentsApi } from '@/api/agents'

export const useAgentsStore = defineStore('agents', () => {
  const archetypes = ref([])
  const agents = ref([])
  const loading = ref(false)
  const error = ref(null)

  const archetypeCount = computed(() => archetypes.value.length)
  const agentCount = computed(() => agents.value.length)

  const archetypesByCategory = computed(() => {
    const grouped = {}
    for (const a of archetypes.value) {
      const cat = a.category || 'other'
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(a)
    }
    return grouped
  })

  async function fetchArchetypes() {
    if (archetypes.value.length > 0) return
    loading.value = true
    error.value = null
    try {
      const { data } = await agentsApi.listArchetypes()
      archetypes.value = data.archetypes || []
    } catch (e) {
      error.value = e.message || 'Failed to load archetypes'
    } finally {
      loading.value = false
    }
  }

  async function createAgent(spec) {
    loading.value = true
    error.value = null
    try {
      const { data } = await agentsApi.create(spec)
      if (data.agent) agents.value.push(data.agent)
      return data.agent
    } catch (e) {
      error.value = e.message || 'Failed to create agent'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createBatch(distribution, options = {}) {
    loading.value = true
    error.value = null
    try {
      const { data } = await agentsApi.createBatch({
        distribution,
        ...options,
      })
      agents.value.push(...(data.agents || []))
      return data.agents
    } catch (e) {
      error.value = e.message || 'Failed to create batch'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createFromScenario(agentConfig, options = {}) {
    loading.value = true
    error.value = null
    try {
      const { data } = await agentsApi.createFromScenario({
        agent_config: agentConfig,
        ...options,
      })
      agents.value.push(...(data.agents || []))
      return data.agents
    } catch (e) {
      error.value = e.message || 'Failed to create agents from scenario'
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearAgents() {
    agents.value = []
  }

  function reset() {
    archetypes.value = []
    agents.value = []
    loading.value = false
    error.value = null
  }

  return {
    archetypes,
    agents,
    loading,
    error,
    archetypeCount,
    agentCount,
    archetypesByCategory,
    fetchArchetypes,
    createAgent,
    createBatch,
    createFromScenario,
    clearAgents,
    reset,
  }
})
