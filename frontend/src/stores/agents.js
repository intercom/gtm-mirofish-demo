import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { agentsApi } from '../api/agents'

const STORAGE_KEY = 'mirofish_agents'

function loadStoredAgents() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref(loadStoredAgents())
  const loading = ref(false)
  const error = ref(null)

  const hasAgents = computed(() => agents.value.length > 0)

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(agents.value))
    } catch {
      // Storage full or unavailable
    }
  }

  async function fetchAgents(force = false) {
    if (agents.value.length > 0 && !force) return agents.value

    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.list()
      agents.value = res.data?.agents || res.data || []
      persist()
      return agents.value
    } catch (e) {
      error.value = e.message
      return agents.value
    } finally {
      loading.value = false
    }
  }

  async function createAgent(agentData) {
    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.create(agentData)
      const created = res.data?.agent || res.data
      agents.value.push(created)
      persist()
      return created
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateAgent(id, agentData) {
    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.update(id, agentData)
      const updated = res.data?.agent || res.data
      const idx = agents.value.findIndex((a) => a.id === id)
      if (idx !== -1) agents.value[idx] = updated
      persist()
      return updated
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteAgent(id) {
    loading.value = true
    error.value = null
    try {
      await agentsApi.delete(id)
      agents.value = agents.value.filter((a) => a.id !== id)
      persist()
      return true
    } catch (e) {
      error.value = e.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function cloneAgent(id) {
    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.clone(id)
      const cloned = res.data?.agent || res.data
      agents.value.push(cloned)
      persist()
      return cloned
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  function addLocal(agentData) {
    const agent = {
      id: `local-${Date.now()}`,
      ...agentData,
      createdAt: new Date().toISOString(),
    }
    agents.value.push(agent)
    persist()
    return agent
  }

  function reset() {
    agents.value = []
    loading.value = false
    error.value = null
    persist()
  }

  return {
    agents,
    loading,
    error,
    hasAgents,
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    cloneAgent,
    addLocal,
    reset,
  }
})
