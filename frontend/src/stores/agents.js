import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { agentsApi } from '../api/agents'

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref([])
  const templates = ref([])
  const loading = ref(false)
  const error = ref(null)

  const hasAgents = computed(() => agents.value.length > 0)

  async function fetchAgents(force = false) {
    if (agents.value.length > 0 && !force) return agents.value

    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.list()
      agents.value = res.data?.data || []
      return agents.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchTemplates(force = false) {
    if (templates.value.length > 0 && !force) return templates.value

    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.templates()
      templates.value = res.data?.data || []
      return templates.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data) {
    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.create(data)
      const created = res.data?.data
      if (created) agents.value.unshift(created)
      return created
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateAgent(agentId, data) {
    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.update(agentId, data)
      const updated = res.data?.data
      if (updated) {
        const idx = agents.value.findIndex((a) => a.id === agentId)
        if (idx !== -1) agents.value[idx] = updated
      }
      return updated
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteAgent(agentId) {
    loading.value = true
    error.value = null
    try {
      await agentsApi.delete(agentId)
      agents.value = agents.value.filter((a) => a.id !== agentId)
      return true
    } catch (e) {
      error.value = e.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function cloneAgent(agentId) {
    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.clone(agentId)
      const cloned = res.data?.data
      if (cloned) agents.value.unshift(cloned)
      return cloned
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function generateAgent(description) {
    loading.value = true
    error.value = null
    try {
      const res = await agentsApi.generate(description)
      return res.data?.data || null
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    agents,
    templates,
    loading,
    error,
    hasAgents,
    fetchAgents,
    fetchTemplates,
    createAgent,
    updateAgent,
    deleteAgent,
    cloneAgent,
    generateAgent,
  }
})
