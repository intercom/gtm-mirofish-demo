import { ref, computed, onMounted, onUnmounted } from 'vue'
import client from '../api/client'

const POLL_INTERVAL = 60_000

const services = ref({
  backend: { status: 'unknown' },
  llm: { status: 'unknown' },
  zep: { status: 'unknown' },
})
const loading = ref(false)
const lastChecked = ref(null)

let timer = null
let subscribers = 0

async function check() {
  loading.value = true
  try {
    const { data } = await client.get('/services/status')
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

function startPolling() {
  if (timer) return
  check()
  timer = setInterval(check, POLL_INTERVAL)
}

function stopPolling() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

export function useServiceStatus() {
  const isAllOk = computed(() =>
    Object.values(services.value).every((s) => s.status === 'ok'),
  )

  const isDemoMode = computed(() =>
    Object.values(services.value).some((s) => s.status === 'unconfigured'),
  )

  const isBackendReachable = computed(() => services.value.backend.status === 'ok')

  onMounted(() => {
    subscribers++
    if (subscribers === 1) startPolling()
  })

  onUnmounted(() => {
    subscribers--
    if (subscribers <= 0) {
      subscribers = 0
      stopPolling()
    }
  })

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
