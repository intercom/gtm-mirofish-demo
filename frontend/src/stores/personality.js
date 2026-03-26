import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { personalityApi } from '@/api/personality'

export const usePersonalityStore = defineStore('personality', () => {
  const agents = ref({})
  const trajectories = ref({})
  const traits = ref(['analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant'])
  const bounds = ref({ min: 20, max: 80 })
  const loading = ref(false)
  const error = ref(null)
  const selectedAgentId = ref(null)

  const agentIds = computed(() => Object.keys(agents.value))
  const selectedAgent = computed(() => agents.value[selectedAgentId.value] || null)
  const selectedTrajectory = computed(() => trajectories.value[selectedAgentId.value] || [])

  async function fetchAgents(simulationId) {
    loading.value = true
    error.value = null
    try {
      const res = await personalityApi.listAgents(simulationId)
      if (res.data?.success) {
        agents.value = res.data.data.agents
        traits.value = res.data.data.traits
        bounds.value = res.data.data.bounds
        if (!selectedAgentId.value && Object.keys(agents.value).length) {
          selectedAgentId.value = Object.keys(agents.value)[0]
        }
      }
    } catch (e) {
      error.value = e.message || 'Failed to fetch agents'
    } finally {
      loading.value = false
    }
  }

  async function fetchTrajectory(simulationId, agentId) {
    try {
      const res = await personalityApi.getTrajectory(simulationId, agentId)
      if (res.data?.success) {
        trajectories.value[agentId] = res.data.data.trajectory
      }
    } catch (e) {
      error.value = e.message || 'Failed to fetch trajectory'
    }
  }

  function selectAgent(agentId) {
    selectedAgentId.value = agentId
  }

  function $reset() {
    agents.value = {}
    trajectories.value = {}
    selectedAgentId.value = null
    loading.value = false
    error.value = null
  }

  return {
    agents,
    trajectories,
    traits,
    bounds,
    loading,
    error,
    selectedAgentId,
    agentIds,
    selectedAgent,
    selectedTrajectory,
    fetchAgents,
    fetchTrajectory,
    selectAgent,
    $reset,
  }
})
