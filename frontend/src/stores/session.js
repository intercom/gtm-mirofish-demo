import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { sessionsApi } from '../api/sessions'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref([])
  const activeSession = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const activeSessionId = computed(() => activeSession.value?.session_id ?? null)
  const hasSessions = computed(() => sessions.value.length > 0)

  async function fetchSessions(params = {}) {
    loading.value = true
    error.value = null
    try {
      const { data } = await sessionsApi.list(params)
      sessions.value = data.sessions
      return data.sessions
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function createSession(payload) {
    error.value = null
    try {
      const { data } = await sessionsApi.create(payload)
      sessions.value.unshift(data)
      activeSession.value = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function loadSession(sessionId) {
    loading.value = true
    error.value = null
    try {
      const { data } = await sessionsApi.get(sessionId)
      activeSession.value = data
      // Update the list entry if present
      const idx = sessions.value.findIndex(s => s.session_id === sessionId)
      if (idx !== -1) sessions.value[idx] = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateSession(sessionId, payload) {
    error.value = null
    try {
      const { data } = await sessionsApi.update(sessionId, payload)
      // Update active session if it matches
      if (activeSession.value?.session_id === sessionId) {
        activeSession.value = data
      }
      const idx = sessions.value.findIndex(s => s.session_id === sessionId)
      if (idx !== -1) sessions.value[idx] = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function deleteSession(sessionId) {
    error.value = null
    try {
      await sessionsApi.delete(sessionId)
      sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
      if (activeSession.value?.session_id === sessionId) {
        activeSession.value = null
      }
      return true
    } catch (e) {
      error.value = e.message
      return false
    }
  }

  async function addSimulation(sessionId, simulationId) {
    error.value = null
    try {
      const { data } = await sessionsApi.addSimulation(sessionId, simulationId)
      if (activeSession.value?.session_id === sessionId) {
        activeSession.value = data
      }
      const idx = sessions.value.findIndex(s => s.session_id === sessionId)
      if (idx !== -1) sessions.value[idx] = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  function setActiveSession(session) {
    activeSession.value = session
  }

  function clearActiveSession() {
    activeSession.value = null
  }

  function $reset() {
    sessions.value = []
    activeSession.value = null
    loading.value = false
    error.value = null
  }

  return {
    sessions,
    activeSession,
    loading,
    error,
    activeSessionId,
    hasSessions,
    fetchSessions,
    createSession,
    loadSession,
    updateSession,
    deleteSession,
    addSimulation,
    setActiveSession,
    clearActiveSession,
    $reset,
  }
})
