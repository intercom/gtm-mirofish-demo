import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import client from '../api/client'

export const usePersonasStore = defineStore('personas', () => {
  const personas = ref([])
  const loading = ref(false)
  const generating = ref(false)
  const error = ref(null)

  const hasPersonas = computed(() => personas.value.length > 0)

  async function fetchPersonas(source = null) {
    loading.value = true
    error.value = null
    try {
      const params = source ? { source } : {}
      const res = await client.get('/agents/personas', { params })
      personas.value = res.data.personas || []
      return personas.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function getPersona(id) {
    loading.value = true
    error.value = null
    try {
      const res = await client.get(`/agents/personas/${id}`)
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function generatePersonas({ scenarioType, numAgents = 4, roleDistribution = null, personalityDiversity = 0.5 }) {
    generating.value = true
    error.value = null
    try {
      const res = await client.post('/agents/personas/generate', {
        scenario_type: scenarioType,
        num_agents: numAgents,
        role_distribution: roleDistribution,
        personality_diversity: personalityDiversity,
      })
      const generated = res.data.personas || []
      personas.value = [...personas.value, ...generated]
      return generated
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      generating.value = false
    }
  }

  async function updatePersona(id, updates) {
    error.value = null
    try {
      const res = await client.put(`/agents/personas/${id}`, updates)
      const updated = res.data
      const idx = personas.value.findIndex((p) => p.id === id)
      if (idx !== -1) personas.value[idx] = updated
      return updated
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function clonePersona(id, overrides = {}) {
    error.value = null
    try {
      const res = await client.post(`/agents/personas/${id}/clone`, overrides)
      const cloned = res.data
      personas.value.push(cloned)
      return cloned
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  function clearPersonas() {
    personas.value = []
    error.value = null
  }

  return {
    personas,
    loading,
    generating,
    error,
    hasPersonas,
    fetchPersonas,
    getPersona,
    generatePersonas,
    updatePersona,
    clonePersona,
    clearPersonas,
  }
})
