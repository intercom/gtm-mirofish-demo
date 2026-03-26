import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish_memory_bundles'

function loadStoredBundles() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const useMemoryTransferStore = defineStore('memoryTransfer', () => {
  const bundles = ref(loadStoredBundles())
  const activeBundleId = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const lastExport = ref(null)
  const lastImport = ref(null)

  const activeBundle = computed(() =>
    bundles.value.find(b => b.bundle_id === activeBundleId.value) || null
  )

  const bundleCount = computed(() => bundles.value.length)

  const exportedBundles = computed(() =>
    bundles.value.filter(b => !b.is_import)
  )

  const importedBundles = computed(() =>
    bundles.value.filter(b => b.is_import)
  )

  function setBundles(newBundles) {
    bundles.value = newBundles
    _persist()
  }

  function addBundle(bundle) {
    const existing = bundles.value.findIndex(b => b.bundle_id === bundle.bundle_id)
    if (existing !== -1) {
      bundles.value[existing] = bundle
    } else {
      bundles.value.push(bundle)
    }
    _persist()
  }

  function removeBundle(bundleId) {
    const idx = bundles.value.findIndex(b => b.bundle_id === bundleId)
    if (idx !== -1) bundles.value.splice(idx, 1)
    if (activeBundleId.value === bundleId) activeBundleId.value = null
    _persist()
  }

  function selectBundle(bundleId) {
    activeBundleId.value = bundleId
  }

  function setLoading(val) {
    loading.value = val
  }

  function setError(msg) {
    error.value = msg
  }

  function setLastExport(bundle) {
    lastExport.value = bundle
  }

  function setLastImport(receipt) {
    lastImport.value = receipt
  }

  function reset() {
    bundles.value = []
    activeBundleId.value = null
    loading.value = false
    error.value = null
    lastExport.value = null
    lastImport.value = null
    _persist()
  }

  function _persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(bundles.value))
    } catch {
      // Storage full — silently ignore
    }
  }

  return {
    bundles,
    activeBundleId,
    loading,
    error,
    lastExport,
    lastImport,
    activeBundle,
    bundleCount,
    exportedBundles,
    importedBundles,
    setBundles,
    addBundle,
    removeBundle,
    selectBundle,
    setLoading,
    setError,
    setLastExport,
    setLastImport,
    reset,
  }
})
