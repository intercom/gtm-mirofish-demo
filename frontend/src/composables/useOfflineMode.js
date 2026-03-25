import { ref, computed, provide, inject, onUnmounted } from 'vue'
import { API_BASE } from '../api/client'

export const OFFLINE_KEY = Symbol('offlineMode')
export const HEALTH_INTERVAL = 30_000
export const HEALTH_TIMEOUT = 5_000

// Module-scoped singleton state — shared across all consumers
const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const connectionType = ref(
  typeof navigator !== 'undefined' && navigator.connection
    ? navigator.connection.effectiveType
    : 'unknown',
)
const lastOnline = ref(isOnline.value ? new Date() : null)

let healthTimer = null
let initialized = false

export async function checkConnectivity() {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), HEALTH_TIMEOUT)
  try {
    await fetch(`${API_BASE}/health`, {
      method: 'HEAD',
      cache: 'no-store',
      signal: controller.signal,
    })
    // Any response (even 404) means server is reachable
    isOnline.value = true
    lastOnline.value = new Date()
  } catch {
    isOnline.value = false
  } finally {
    clearTimeout(timeout)
  }
}

export function handleOnline() {
  isOnline.value = true
  lastOnline.value = new Date()
  checkConnectivity()
}

export function handleOffline() {
  isOnline.value = false
}

function updateConnectionType() {
  connectionType.value = navigator.connection?.effectiveType || 'unknown'
}

export function setup() {
  if (initialized) return
  initialized = true

  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  if (navigator.connection) {
    navigator.connection.addEventListener('change', updateConnectionType)
  }

  checkConnectivity()
  healthTimer = setInterval(checkConnectivity, HEALTH_INTERVAL)
}

export function teardown() {
  if (!initialized) return
  initialized = false

  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  if (navigator.connection) {
    navigator.connection.removeEventListener('change', updateConnectionType)
  }
  clearInterval(healthTimer)
  healthTimer = null
}

export function isInitialized() {
  return initialized
}

const state = {
  isOnline,
  isOffline: computed(() => !isOnline.value),
  connectionType,
  lastOnline,
  checkConnectivity,
}

/**
 * Call in root component (App.vue) to provide offline state app-wide via inject.
 */
export function provideOfflineMode() {
  setup()
  provide(OFFLINE_KEY, state)
  onUnmounted(teardown)
  return state
}

/**
 * Use in any component. Tries inject first, falls back to module-scoped state.
 */
export function useOfflineMode() {
  const injected = inject(OFFLINE_KEY, null)
  if (injected) return injected

  if (!initialized) setup()
  return state
}
