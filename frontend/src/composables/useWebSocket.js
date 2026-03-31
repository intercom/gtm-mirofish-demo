import { ref, readonly, onUnmounted, getCurrentInstance } from 'vue'
import { io } from 'socket.io-client'
import { API_BASE } from '../api/client'

function resolveServerUrl() {
  const explicit = import.meta.env.VITE_WS_URL
  if (explicit) return explicit

  if (API_BASE.startsWith('http')) {
    return API_BASE.replace(/\/api\/?$/, '')
  }

  // Relative API path — socket.io will connect to current origin
  // (works with Vite proxy in dev and same-origin deploys in prod)
  return undefined
}

// Module-level shared state — one socket connection for the whole app
const connected = ref(false)
const reconnecting = ref(false)
const disconnected = ref(true)
const error = ref(null)
let socket = null

function bindSocketEvents() {
  socket.on('connect', () => {
    connected.value = true
    reconnecting.value = false
    disconnected.value = false
    error.value = null
  })

  socket.on('disconnect', () => {
    connected.value = false
    disconnected.value = true
  })

  socket.on('connect_error', (err) => {
    connected.value = false
    error.value = err.message || 'Connection failed'
  })

  socket.on('error', (data) => {
    error.value = data?.message || data || 'Server error'
  })

  socket.io.on('reconnect_attempt', () => {
    reconnecting.value = true
    disconnected.value = false
  })

  socket.io.on('reconnect', () => {
    reconnecting.value = false
  })

  socket.io.on('reconnect_failed', () => {
    reconnecting.value = false
    disconnected.value = true
    error.value = 'Max reconnection attempts reached'
  })
}

export function useWebSocket(options = {}) {
  // Per-component handler tracking for cleanup on unmount
  const localHandlers = []

  function connect(simulationId) {
    if (socket?.connected) {
      if (simulationId) {
        socket.emit('join_simulation', { simulation_id: simulationId })
      }
      return
    }

    if (socket) {
      socket.connect()
      return
    }

    socket = io(resolveServerUrl(), {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 30000,
      reconnectionAttempts: 10,
      transports: ['websocket', 'polling'],
      autoConnect: true,
      ...options,
    })

    bindSocketEvents()

    if (simulationId) {
      socket.on('connect', () => {
        socket.emit('join_simulation', { simulation_id: simulationId })
      })
    }
  }

  function disconnect() {
    if (!socket) return
    socket.disconnect()
    socket = null
    connected.value = false
    reconnecting.value = false
    disconnected.value = true
    error.value = null
  }

  function joinSimulation(id) {
    socket?.emit('join_simulation', { simulation_id: id })
  }

  function leaveSimulation(id) {
    socket?.emit('leave_simulation', { simulation_id: id })
  }

  function subscribeData(type) {
    socket?.emit('subscribe_data', { type })
  }

  function on(event, handler) {
    if (!socket) return () => {}
    socket.on(event, handler)
    localHandlers.push({ event, handler })
    return () => off(event, handler)
  }

  function off(event, handler) {
    if (!socket) return
    socket.off(event, handler)
    const idx = localHandlers.findIndex(
      (h) => h.event === event && h.handler === handler,
    )
    if (idx !== -1) localHandlers.splice(idx, 1)
  }

  function emit(event, data) {
    socket?.emit(event, data)
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

  // Clean up this component's listeners on unmount (only inside setup)
  if (getCurrentInstance()) {
    onUnmounted(() => {
      for (const { event, handler } of localHandlers) {
        socket?.off(event, handler)
      }
      localHandlers.length = 0
    })
  }

  return {
    connected: readonly(connected),
    reconnecting: readonly(reconnecting),
    disconnected: readonly(disconnected),
    error: readonly(error),
    connect,
    disconnect,
    joinSimulation,
    leaveSimulation,
    subscribeData,
    on,
    off,
    emit,
    onRoundComplete,
    onAgentMessage,
    onMetricUpdate,
    onStatusChange,
  }
}
