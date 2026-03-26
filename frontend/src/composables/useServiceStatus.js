import { ref, onMounted, onUnmounted } from 'vue'
import client from '../api/client'

const POLL_INTERVAL = 60_000

const status = ref(null)
const loading = ref(false)
const error = ref(null)
const lastChecked = ref(null)

let timer = null
let subscribers = 0

async function fetch_status() {
  loading.value = true
  error.value = null
  try {
    const { data: res } = await client.get('/settings/service-status')
    status.value = res.data
    lastChecked.value = new Date()
  } catch (e) {
    error.value = e.message || 'Backend unreachable'
    status.value = { overall: 'unreachable', services: {} }
  } finally {
    loading.value = false
  }
}

function startPolling() {
  if (timer) return
  fetch_status()
  timer = setInterval(fetch_status, POLL_INTERVAL)
}

function stopPolling() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

export function useServiceStatus() {
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

  return { status, loading, error, lastChecked, refresh: fetch_status }
}
