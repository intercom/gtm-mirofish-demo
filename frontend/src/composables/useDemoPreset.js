import { ref } from 'vue'
import { demoPresetApi } from '../api/demoPreset'

const available = ref(false)
const loaded = ref(false)
const loading = ref(false)
const presetIds = ref({ simulationId: null, reportId: null, graphTaskId: null })
const error = ref(null)

export function useDemoPreset() {
  async function checkStatus() {
    try {
      const { data } = await demoPresetApi.getStatus()
      const d = data.data || data
      available.value = d.available
      loaded.value = d.loaded
      if (d.loaded) {
        presetIds.value = {
          simulationId: d.simulation_id,
          reportId: d.report_id,
          graphTaskId: 'demo-graph-preset',
        }
      }
    } catch (e) {
      error.value = e.message
    }
  }

  async function loadPreset() {
    if (loading.value) return
    loading.value = true
    error.value = null
    try {
      const { data } = await demoPresetApi.load()
      const d = data.data || data
      loaded.value = true
      presetIds.value = {
        simulationId: d.simulation_id,
        reportId: d.report_id,
        graphTaskId: d.graph_task_id,
      }
      return presetIds.value
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    available,
    loaded,
    loading,
    presetIds,
    error,
    checkStatus,
    loadPreset,
  }
}
