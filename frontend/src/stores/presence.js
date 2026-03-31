import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const usePresenceStore = defineStore('presence', () => {
  const users = ref([])
  const cursors = ref([])
  const events = ref([])
  const totalOnline = ref(0)
  const lastEventTimestamp = ref(0)
  const error = ref(null)

  const activeUsers = computed(() =>
    users.value.filter(u => u.status !== 'idle'),
  )

  const usersByPage = computed(() => {
    const map = {}
    for (const u of users.value) {
      const page = u.current_page || 'Unknown'
      if (!map[page]) map[page] = []
      map[page].push(u)
    }
    return map
  })

  function setPresence(data) {
    users.value = data.users || []
    totalOnline.value = data.total_online || 0
  }

  function setCursors(data) {
    cursors.value = data.cursors || []
  }

  function addEvents(newEvents) {
    events.value = [...events.value, ...newEvents].slice(-100)
    if (newEvents.length > 0) {
      lastEventTimestamp.value = newEvents[newEvents.length - 1].timestamp
    }
  }

  function setError(msg) {
    error.value = msg
  }

  function reset() {
    users.value = []
    cursors.value = []
    events.value = []
    totalOnline.value = 0
    lastEventTimestamp.value = 0
    error.value = null
  }

  return {
    users,
    cursors,
    events,
    totalOnline,
    lastEventTimestamp,
    error,
    activeUsers,
    usersByPage,
    setPresence,
    setCursors,
    addEvents,
    setError,
    reset,
  }
})
