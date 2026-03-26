import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { personasApi } from '../api/personas'

export const usePersonasStore = defineStore('personas', () => {
  const personas = ref([])
  const loading = ref(false)
  const error = ref(null)
  const generationSource = ref(null) // "zep_graph" | "template"

  const count = computed(() => personas.value.length)
  const hasPersonas = computed(() => personas.value.length > 0)

  const byRole = computed(() => {
    const map = {}
    for (const p of personas.value) {
      const role = p.title || 'Unknown'
      if (!map[role]) map[role] = []
      map[role].push(p)
    }
    return map
  })

  async function generate(scenario, numAgents = 10, graphId = null) {
    loading.value = true
    error.value = null
    try {
      const payload = { scenario, num_agents: numAgents }
      if (graphId) payload.graph_id = graphId
      const { data } = await personasApi.generate(payload)
      personas.value = data.personas || []
      generationSource.value = data.source || 'template'
      return personas.value
    } catch (e) {
      error.value = e.message || 'Failed to generate personas'
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const { data } = await personasApi.list()
      personas.value = data.personas || []
      return personas.value
    } catch (e) {
      error.value = e.message || 'Failed to fetch personas'
      return []
    } finally {
      loading.value = false
    }
  }

  async function updatePersona(id, updates) {
    try {
      const { data } = await personasApi.update(id, updates)
      if (data.persona) {
        const idx = personas.value.findIndex((p) => p.id === id)
        if (idx !== -1) personas.value[idx] = data.persona
      }
      return data.persona
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function enhancePersona(id, simulationContext) {
    try {
      const { data } = await personasApi.enhance(id, simulationContext)
      if (data.persona) {
        const idx = personas.value.findIndex((p) => p.id === id)
        if (idx !== -1) personas.value[idx] = data.persona
      }
      return data.persona
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  function clear() {
    personas.value = []
    generationSource.value = null
    error.value = null
  }

  return {
    personas,
    loading,
    error,
    generationSource,
    count,
    hasPersonas,
    byRole,
    generate,
    fetchAll,
    updatePersona,
    enhancePersona,
    clear,
  }
})
