import { ref, onUnmounted, toValue } from 'vue'
import { API_BASE } from '../api/client'

/**
 * Composable for managing a Server-Sent Events connection to the
 * simulation live feed endpoint. Provides a reactive array of events
 * and connection status, with automatic reconnection on failure.
 *
 * @param {Ref<string>|string|Function} taskIdSource - reactive task ID
 * @returns {{ events, status, streamStatus, connect, disconnect, clear }}
 */
export function useSimulationStream(taskIdSource) {
  const events = ref([])
  const status = ref('disconnected') // 'disconnected' | 'connecting' | 'connected' | 'done' | 'error'
  const streamStatus = ref(null) // latest status event from server

  let eventSource = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  const MAX_EVENTS = 500
  const MAX_RECONNECT_ATTEMPTS = 5

  function connect() {
    const taskId = toValue(taskIdSource)
    if (!taskId) return

    disconnect()
    status.value = 'connecting'

    const fromIndex = events.value.length
    const url = `${API_BASE}/simulation/${taskId}/feed?from_index=${fromIndex}`
    eventSource = new EventSource(url)

    eventSource.addEventListener('connected', () => {
      status.value = 'connected'
      reconnectAttempts = 0
    })

    eventSource.addEventListener('action', (e) => {
      try {
        const action = JSON.parse(e.data)
        events.value.push(action)
        if (events.value.length > MAX_EVENTS) {
          events.value = events.value.slice(-MAX_EVENTS)
        }
      } catch {
        // Ignore malformed events
      }
    })

    eventSource.addEventListener('status', (e) => {
      try {
        streamStatus.value = JSON.parse(e.data)
      } catch {
        // Ignore
      }
    })

    eventSource.addEventListener('done', () => {
      status.value = 'done'
      closeSource()
    })

    eventSource.addEventListener('error', () => {
      if (status.value === 'done') return
      status.value = 'error'
      closeSource()
      scheduleReconnect()
    })

    eventSource.onerror = () => {
      if (status.value === 'done') return
      status.value = 'error'
      closeSource()
      scheduleReconnect()
    }
  }

  function closeSource() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  function disconnect() {
    closeSource()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    reconnectAttempts = 0
  }

  function scheduleReconnect() {
    if (reconnectTimer || status.value === 'done') return
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      status.value = 'error'
      return
    }
    reconnectAttempts++
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000)
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  function clear() {
    events.value = []
  }

  onUnmounted(disconnect)

  return {
    events,
    status,
    streamStatus,
    connect,
    disconnect,
    clear,
  }
}
