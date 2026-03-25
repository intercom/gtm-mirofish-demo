import { ref, computed } from 'vue'
import client from '../api/client'

const services = ref({
  backend: { status: 'unknown' },
  llm: { status: 'unknown' },
  zep: { status: 'unknown' },
})
const loading = ref(false)
const lastChecked = ref(null)

export function useServiceStatus() {
  const isAllOk = computed(() =>
    Object.values(services.value).every((s) => s.status === 'ok'),
  )

  const isDemoMode = computed(() =>
    Object.values(services.value).some((s) => s.status === 'unconfigured'),
  )

  const isBackendReachable = computed(() => services.value.backend.status === 'ok')

  async function check() {
    loading.value = true
    try {
      const { data } = await client.get('/api/v1/services/status')
      services.value = data.services
      lastChecked.value = Date.now()
    } catch {
      services.value = {
        backend: { status: 'error', message: 'Backend unreachable' },
        llm: { status: 'unknown' },
        zep: { status: 'unknown' },
      }
      lastChecked.value = Date.now()
    } finally {
      loading.value = false
    }
  }

  return {
    services,
    loading,
    lastChecked,
    isAllOk,
    isDemoMode,
    isBackendReachable,
    check,
  }
}
