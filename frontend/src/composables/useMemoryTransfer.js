import { ref } from 'vue'
import { memoryTransferApi } from '../api/memoryTransfer'
import { useMemoryTransferStore } from '../stores/memoryTransfer'

/**
 * Composable for cross-simulation memory transfer operations.
 * Wraps API calls with loading/error state and store updates.
 */
export function useMemoryTransfer() {
  const store = useMemoryTransferStore()
  const exporting = ref(false)
  const importing = ref(false)
  const transferring = ref(false)

  async function exportMemory(simulationId, agentId, filterType = 'all') {
    exporting.value = true
    store.setError(null)
    try {
      const res = await memoryTransferApi.exportMemory({
        simulation_id: simulationId,
        agent_id: agentId,
        filter_type: filterType,
      })
      if (res.data?.success) {
        const bundle = res.data.data
        store.addBundle(bundle)
        store.setLastExport(bundle)
        return bundle
      }
      throw new Error(res.data?.error || 'Export failed')
    } catch (err) {
      store.setError(err.message || 'Export failed')
      return null
    } finally {
      exporting.value = false
    }
  }

  async function importMemory(simulationId, agentId, bundle) {
    importing.value = true
    store.setError(null)
    try {
      const res = await memoryTransferApi.importMemory({
        simulation_id: simulationId,
        agent_id: agentId,
        bundle,
      })
      if (res.data?.success) {
        const receipt = res.data.data
        store.setLastImport(receipt)
        return receipt
      }
      throw new Error(res.data?.error || 'Import failed')
    } catch (err) {
      store.setError(err.message || 'Import failed')
      return null
    } finally {
      importing.value = false
    }
  }

  async function transferMemory(agentId, fromSimId, toSimId, filterType = 'all') {
    transferring.value = true
    store.setError(null)
    try {
      const res = await memoryTransferApi.transfer({
        agent_id: agentId,
        from_simulation_id: fromSimId,
        to_simulation_id: toSimId,
        filter_type: filterType,
      })
      if (res.data?.success) {
        const result = res.data.data
        store.addBundle(result.bundle)
        store.setLastExport(result.bundle)
        store.setLastImport(result.import_receipt)
        return result
      }
      throw new Error(res.data?.error || 'Transfer failed')
    } catch (err) {
      store.setError(err.message || 'Transfer failed')
      return null
    } finally {
      transferring.value = false
    }
  }

  async function loadBundles(simulationId) {
    store.setLoading(true)
    store.setError(null)
    try {
      const res = await memoryTransferApi.listBundles(simulationId)
      if (res.data?.success) {
        store.setBundles(res.data.data)
        return res.data.data
      }
      throw new Error(res.data?.error || 'Failed to load bundles')
    } catch (err) {
      // Fallback to demo bundles on failure
      try {
        const demo = await memoryTransferApi.getDemoBundles()
        if (demo.data?.success) {
          store.setBundles(demo.data.data)
          return demo.data.data
        }
      } catch {
        // ignore demo fallback failure
      }
      store.setError(err.message || 'Failed to load bundles')
      return []
    } finally {
      store.setLoading(false)
    }
  }

  async function loadDemoBundles() {
    store.setLoading(true)
    store.setError(null)
    try {
      const res = await memoryTransferApi.getDemoBundles()
      if (res.data?.success) {
        store.setBundles(res.data.data)
        return res.data.data
      }
      throw new Error(res.data?.error || 'Failed to load demo bundles')
    } catch (err) {
      store.setError(err.message || 'Failed to load demo bundles')
      return []
    } finally {
      store.setLoading(false)
    }
  }

  async function deleteBundle(simulationId, bundleId) {
    store.setError(null)
    try {
      const res = await memoryTransferApi.deleteBundle(simulationId, bundleId)
      if (res.data?.success) {
        store.removeBundle(bundleId)
        return true
      }
      throw new Error(res.data?.error || 'Delete failed')
    } catch (err) {
      store.setError(err.message || 'Delete failed')
      return false
    }
  }

  return {
    exporting,
    importing,
    transferring,
    exportMemory,
    importMemory,
    transferMemory,
    loadBundles,
    loadDemoBundles,
    deleteBundle,
  }
}
