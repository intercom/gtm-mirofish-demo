import { ref, computed } from 'vue'
import { cacheApi } from '../api/cache'

/**
 * Composable for simulation result caching and offline replay.
 *
 * Provides two capabilities:
 * 1. CRUD operations on the cache (list, save, delete)
 * 2. Loading a cached snapshot into reactive refs that match the
 *    shape of useSimulationPolling — so UI components can render
 *    cached results identically to live results.
 */
export function useSimulationCache() {
  const cachedList = ref([])
  const loading = ref(false)
  const error = ref(null)

  // --- Replay state (mirrors useSimulationPolling shape) ---
  const replayActive = ref(false)
  const replayId = ref(null)
  const replayRunState = ref(null)
  const replayActions = ref([])
  const replayTimeline = ref([])
  const replayMetadata = ref(null)

  const replaySimStatus = computed(() =>
    replayActive.value ? 'completed' : 'idle',
  )

  // --- Cache CRUD ---

  async function fetchList() {
    loading.value = true
    error.value = null
    try {
      const res = await cacheApi.list()
      cachedList.value = res.data?.data || []
    } catch (err) {
      error.value = err.message || 'Failed to load cache list'
    } finally {
      loading.value = false
    }
  }

  async function cacheSimulation(simulationId) {
    error.value = null
    try {
      const res = await cacheApi.create(simulationId)
      await fetchList()
      return res.data?.data
    } catch (err) {
      error.value = err.message || 'Failed to cache simulation'
      throw err
    }
  }

  async function deleteCached(simulationId) {
    error.value = null
    try {
      await cacheApi.delete(simulationId)
      cachedList.value = cachedList.value.filter((e) => e.id !== simulationId)
      if (replayId.value === simulationId) stopReplay()
    } catch (err) {
      error.value = err.message || 'Failed to delete cache'
      throw err
    }
  }

  // --- Replay ---

  async function loadReplay(simulationId) {
    loading.value = true
    error.value = null
    try {
      const res = await cacheApi.get(simulationId)
      const entry = res.data?.data
      if (!entry) throw new Error('Cache entry not found')

      replayId.value = entry.id
      replayRunState.value = entry.run_state || null
      replayActions.value = entry.actions || []
      replayTimeline.value = entry.timeline || []
      replayMetadata.value = entry.metadata || null
      replayActive.value = true
    } catch (err) {
      error.value = err.message || 'Failed to load cached simulation'
      throw err
    } finally {
      loading.value = false
    }
  }

  function stopReplay() {
    replayActive.value = false
    replayId.value = null
    replayRunState.value = null
    replayActions.value = []
    replayTimeline.value = []
    replayMetadata.value = null
  }

  function isCached(simulationId) {
    return cachedList.value.some((e) => e.id === simulationId)
  }

  return {
    // Cache list
    cachedList,
    loading,
    error,
    fetchList,
    cacheSimulation,
    deleteCached,
    isCached,

    // Replay state
    replayActive,
    replayId,
    replayRunState,
    replayActions,
    replayTimeline,
    replayMetadata,
    replaySimStatus,
    loadReplay,
    stopReplay,
  }
}
