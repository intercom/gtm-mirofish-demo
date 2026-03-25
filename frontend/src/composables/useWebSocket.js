import { ref, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { API_BASE } from '../api/client'

/**
 * Derives the Socket.IO server URL from the API base URL.
 * - Full URL (http://host:port/api) → http://host:port
 * - Relative path (/api) → '' (current origin, handled by socket.io-client)
 */
function deriveSocketUrl() {
  try {
    const url = new URL(API_BASE)
    return url.origin
  } catch {
    return ''
  }
}

const SOCKET_URL = deriveSocketUrl()

export function useWebSocket() {
  let socket = null
  let reconnectAttempts = 0
  let reconnectTimer = null
  const listeners = new Map()

  const connected = ref(false)
  const error = ref(null)

  const MAX_RECONNECT_ATTEMPTS = 10
  const BASE_DELAY = 1000
  const MAX_DELAY = 30000

  function connect(simulationId) {
    disconnect()
    error.value = null
    reconnectAttempts = 0

    socket = io(SOCKET_URL, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: false, // we handle reconnection ourselves for backoff control
    })

    socket.on('connect', () => {
      connected.value = true
      error.value = null
      reconnectAttempts = 0

      if (simulationId) {
        socket.emit('join_simulation', { simulation_id: simulationId })
      }
    })

    socket.on('disconnect', (reason) => {
      connected.value = false
      if (reason !== 'io client disconnect') {
        scheduleReconnect(simulationId)
      }
    })

    socket.on('connect_error', (err) => {
      connected.value = false
      error.value = err.message || 'Connection failed'
      scheduleReconnect(simulationId)
    })

    socket.on('error', (data) => {
      error.value = data?.message || data || 'Server error'
    })
  }

  function disconnect() {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
    reconnectAttempts = 0

    if (socket) {
      socket.removeAllListeners()
      socket.disconnect()
      socket = null
    }
    connected.value = false
  }

  function scheduleReconnect(simulationId) {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      error.value = 'Max reconnection attempts reached'
      return
    }

    clearTimeout(reconnectTimer)
    const delay = Math.min(BASE_DELAY * 2 ** reconnectAttempts, MAX_DELAY)
    reconnectAttempts++

    reconnectTimer = setTimeout(() => {
      if (!connected.value) {
        connect(simulationId)
      }
    }, delay)
  }

  function on(event, handler) {
    if (!listeners.has(event)) {
      listeners.set(event, new Set())
    }
    listeners.get(event).add(handler)

    if (socket) {
      socket.on(event, handler)
    }

    return () => off(event, handler)
  }

  function off(event, handler) {
    listeners.get(event)?.delete(handler)
    socket?.off(event, handler)
  }

  function onRoundComplete(callback) {
    return on('round_complete', callback)
  }

  function onAgentMessage(callback) {
    return on('agent_message', callback)
  }

  function onMetricUpdate(callback) {
    return on('metric_update', callback)
  }

  function onStatusChange(callback) {
    return on('simulation_status', callback)
  }

  onUnmounted(() => {
    disconnect()
    listeners.clear()
  })

  return {
    connected,
    error,
    connect,
    disconnect,
    on,
    off,
    onRoundComplete,
    onAgentMessage,
    onMetricUpdate,
    onStatusChange,
  }
}
