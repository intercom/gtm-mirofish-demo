import { ref, onMounted, onUnmounted } from 'vue'
import { presenceApi } from '../api/presence'
import { usePresenceStore } from '../stores/presence'

/**
 * Composable for polling multi-user presence simulation data.
 *
 * Fetches presence state, cursor positions, and events on an interval.
 * Falls back gracefully to demo data if the backend is unreachable.
 */
export function usePresence(options = {}) {
  const {
    pollInterval = 3000,
    cursorInterval = 1000,
    autoStart = true,
  } = options

  const store = usePresenceStore()
  const connected = ref(false)

  let presenceTimer = null
  let cursorTimer = null

  async function fetchPresence() {
    try {
      const res = await presenceApi.getPresence()
      if (res.data?.success) {
        store.setPresence(res.data.data)
        connected.value = true
      }
    } catch {
      connected.value = false
    }
  }

  async function fetchCursors() {
    try {
      const res = await presenceApi.getCursors()
      if (res.data?.success) {
        store.setCursors(res.data.data)
      }
    } catch {
      // Non-critical — cursors just won't update
    }
  }

  async function fetchEvents() {
    try {
      const res = await presenceApi.getEvents(store.lastEventTimestamp)
      if (res.data?.success) {
        store.addEvents(res.data.data.events || [])
      }
    } catch {
      // Non-critical
    }
  }

  function start() {
    stop()
    fetchPresence()
    fetchCursors()
    fetchEvents()
    presenceTimer = setInterval(() => {
      fetchPresence()
      fetchEvents()
    }, pollInterval)
    cursorTimer = setInterval(fetchCursors, cursorInterval)
  }

  function stop() {
    if (presenceTimer) { clearInterval(presenceTimer); presenceTimer = null }
    if (cursorTimer) { clearInterval(cursorTimer); cursorTimer = null }
  }

  onMounted(() => {
    if (autoStart) start()
  })

  onUnmounted(stop)

  return {
    connected,
    start,
    stop,
    fetchPresence,
    fetchCursors,
    fetchEvents,
  }
}
