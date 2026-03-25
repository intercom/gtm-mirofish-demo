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
let socket = null

function bindSocketEvents() {
  socket.on('connect', () => {
    connected.value = true
    reconnecting.value = false
    disconnected.value = false
  })

  socket.on('disconnect', () => {
    connected.value = false
    disconnected.value = true
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
  })
}

export function useWebSocket(options = {}) {
  // Per-component handler tracking for cleanup on unmount
  const localHandlers = []

  function connect() {
    if (socket?.connected) return

    if (socket) {
      socket.connect()
      return
    }

    socket = io(resolveServerUrl(), {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 30000,
      reconnectionAttempts: Infinity,
      transports: ['websocket', 'polling'],
      autoConnect: true,
      ...options,
    })

    bindSocketEvents()
  }

  function disconnect() {
    if (!socket) return
    socket.disconnect()
    socket = null
    connected.value = false
    reconnecting.value = false
    disconnected.value = true
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
    if (!socket) return
    socket.on(event, handler)
    localHandlers.push({ event, handler })
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
    connect,
    disconnect,
    joinSimulation,
    leaveSimulation,
    subscribeData,
    on,
    off,
    emit,
  }
}
