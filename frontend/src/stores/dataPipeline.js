import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { dataPipelineApi } from '../api/dataPipeline'

export const useDataPipelineStore = defineStore('dataPipeline', () => {
  const syncs = ref([])
  const connectors = ref([])
  const dbtModels = ref([])
  const dbtDag = ref({ nodes: [], edges: [] })
  const dbtTests = ref([])
  const freshness = ref([])
  const stats = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // --- Getters ---

  const syncsByConnector = computed(() => {
    const grouped = {}
    for (const sync of syncs.value) {
      const key = sync.connector_name
      if (!grouped[key]) grouped[key] = []
      grouped[key].push(sync)
    }
    return grouped
  })

  const failedSyncs = computed(() =>
    syncs.value.filter((s) => s.status === 'failed'),
  )

  const staleTableCount = computed(() =>
    freshness.value.filter((f) => f.is_stale).length,
  )

  const dbtPassRate = computed(() => {
    if (dbtTests.value.length === 0) return 0
    const passed = dbtTests.value.filter((t) => t.status === 'pass').length
    return Math.round((passed / dbtTests.value.length) * 100)
  })

  const connectorHealthMap = computed(() => {
    const map = {}
    for (const c of connectors.value) {
      map[c.name] = {
        status: c.last_sync_status,
        lastSync: c.last_sync_time,
        successRate: c.success_rate ?? null,
      }
    }
    return map
  })

  // --- Actions ---

  async function fetchSyncs(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await dataPipelineApi.getSyncs(filters)
      syncs.value = res.data?.data?.syncs ?? res.data?.syncs ?? []
      return syncs.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchConnectors() {
    loading.value = true
    error.value = null
    try {
      const res = await dataPipelineApi.getConnectors()
      connectors.value = res.data?.data?.connectors ?? res.data?.connectors ?? []
      return connectors.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchDbtModels() {
    loading.value = true
    error.value = null
    try {
      const res = await dataPipelineApi.getDbtModels()
      dbtModels.value = res.data?.data?.models ?? res.data?.models ?? []
      return dbtModels.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchDbtDag() {
    loading.value = true
    error.value = null
    try {
      const res = await dataPipelineApi.getDbtDag()
      dbtDag.value = res.data?.data?.dag ?? res.data?.dag ?? { nodes: [], edges: [] }
      return dbtDag.value
    } catch (e) {
      error.value = e.message
      return { nodes: [], edges: [] }
    } finally {
      loading.value = false
    }
  }

  async function fetchDbtTests(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await dataPipelineApi.getDbtTests(filters)
      dbtTests.value = res.data?.data?.tests ?? res.data?.tests ?? []
      return dbtTests.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchFreshness() {
    loading.value = true
    error.value = null
    try {
      const res = await dataPipelineApi.getFreshness()
      freshness.value = res.data?.data?.freshness ?? res.data?.freshness ?? []
      return freshness.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchPipelineStats() {
    loading.value = true
    error.value = null
    try {
      const res = await dataPipelineApi.getStats()
      stats.value = res.data?.data?.stats ?? res.data?.stats ?? null
      return stats.value
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    syncs,
    connectors,
    dbtModels,
    dbtDag,
    dbtTests,
    freshness,
    stats,
    loading,
    error,
    syncsByConnector,
    failedSyncs,
    staleTableCount,
    dbtPassRate,
    connectorHealthMap,
    fetchSyncs,
    fetchConnectors,
    fetchDbtModels,
    fetchDbtDag,
    fetchDbtTests,
    fetchFreshness,
    fetchPipelineStats,
    clearError,
  }
})
