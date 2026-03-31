import { ref, computed, onMounted, onUnmounted } from 'vue'
import client, { API_BASE } from '../api/client'
import { useSimulationStore } from '../stores/simulation'

const HEALTH_POLL_INTERVAL = 60_000
const MAX_RESPONSE_TIMES = 10

// Shared state across all consumers
const apiStatus = ref('unknown') // 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
const lastHealthCheck = ref(null)
const responseTimes = ref([])
const healthDetails = ref(null)
let pollTimer = null
let subscribers = 0

// Intercept all axios responses to track latency
let interceptorId = null

function installInterceptor() {
  if (interceptorId !== null) return
  // Tag request start time
  const reqId = client.interceptors.request.use((config) => {
    config._startTime = performance.now()
    return config
  })
  interceptorId = client.interceptors.response.use(
    (response) => {
      if (response.config._startTime) {
        const duration = Math.round(performance.now() - response.config._startTime)
        responseTimes.value = [...responseTimes.value.slice(-(MAX_RESPONSE_TIMES - 1)), duration]
      }
      return response
    },
    (error) => {
      if (error.config?._startTime) {
        const duration = Math.round(performance.now() - error.config._startTime)
        responseTimes.value = [...responseTimes.value.slice(-(MAX_RESPONSE_TIMES - 1)), duration]
      }
      return Promise.reject(error)
    },
  )
  // Store both IDs for cleanup
  interceptorId = { req: reqId, res: interceptorId }
}

async function checkHealth() {
  try {
    const start = performance.now()
    const res = await fetch('/api/v1/health')
    const duration = Math.round(performance.now() - start)
    responseTimes.value = [...responseTimes.value.slice(-(MAX_RESPONSE_TIMES - 1)), duration]
    lastHealthCheck.value = Date.now()

    if (res.ok) {
      const data = await res.json()
      healthDetails.value = data
      apiStatus.value = 'healthy'
    } else {
      apiStatus.value = 'degraded'
    }
  } catch {
    apiStatus.value = 'unhealthy'
  }
}

function startPolling() {
  if (pollTimer) return
  checkHealth()
  pollTimer = setInterval(checkHealth, HEALTH_POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

export function useSystemStatus() {
  const simulation = useSimulationStore()

  const avgResponseTime = computed(() => {
    if (responseTimes.value.length === 0) return null
    const sum = responseTimes.value.reduce((a, b) => a + b, 0)
    return Math.round(sum / responseTimes.value.length)
  })

  const activeSimulationCount = computed(() => (simulation.isActive ? 1 : 0))

  const dataMode = computed(() => {
    if (import.meta.env.VITE_DEMO_MODE === 'true') return 'Demo'
    if (!healthDetails.value) return 'Partial'
    return 'Full'
  })

  const overallHealth = computed(() => {
    if (apiStatus.value === 'unhealthy') return 'unhealthy'
    if (apiStatus.value === 'degraded') return 'degraded'
    if (avgResponseTime.value !== null && avgResponseTime.value > 2000) return 'degraded'
    return apiStatus.value === 'healthy' ? 'healthy' : 'unknown'
  })

  onMounted(() => {
    subscribers++
    installInterceptor()
    startPolling()
  })

  onUnmounted(() => {
    subscribers--
    if (subscribers <= 0) {
      stopPolling()
      subscribers = 0
    }
  })

  return {
    apiStatus,
    lastHealthCheck,
    responseTimes,
    avgResponseTime,
    healthDetails,
    activeSimulationCount,
    dataMode,
    overallHealth,
    apiEndpoint: API_BASE,
    checkHealth,
  }
}
