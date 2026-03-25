import { ref, computed, onUnmounted } from 'vue'
import client from '../api/client'

const services = ref({})
const loading = ref(false)
const lastChecked = ref(null)

let pollTimer = null
let activeInstances = 0

const POLL_INTERVAL = 30_000

async function fetchHealth() {
  try {
    loading.value = true
    const res = await client.get('/v1/health/services')
    services.value = res.data.services || {}
    lastChecked.value = Date.now()
  } catch {
    // Health endpoint unreachable — clear state so consumers see "unknown"
    services.value = {}
  } finally {
    loading.value = false
  }
}

function startPolling() {
  if (!pollTimer) {
    fetchHealth()
    pollTimer = setInterval(fetchHealth, POLL_INTERVAL)
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

/**
 * Reactive service health awareness for the frontend.
 *
 * Polls GET /api/v1/health/services and exposes:
 *  - services        — raw health map { llm: {...}, zep: {...} }
 *  - isDegraded      — true when any service is unhealthy
 *  - degradedServices — array of { name, healthy, configured, error }
 *  - isServiceHealthy(name) — check a specific service
 *
 * Polling starts when the first component mounts and stops when
 * the last one unmounts (ref-counted).
 */
export function useServiceHealth() {
  const isDegraded = computed(() =>
    Object.values(services.value).some((s) => !s.healthy),
  )

  const degradedServices = computed(() =>
    Object.entries(services.value)
      .filter(([, info]) => !info.healthy)
      .map(([name, info]) => ({ name, ...info })),
  )

  const isServiceHealthy = (name) => services.value[name]?.healthy ?? null

  activeInstances++
  startPolling()

  onUnmounted(() => {
    activeInstances--
    if (activeInstances <= 0) {
      stopPolling()
      activeInstances = 0
    }
  })

  return {
    services,
    isDegraded,
    degradedServices,
    isServiceHealthy,
    loading,
    lastChecked,
    refresh: fetchHealth,
  }
}
