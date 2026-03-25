import { onMounted } from 'vue'
import { useSessionStore } from '../stores/session'

/**
 * Composable for session lifecycle management in components.
 * Optionally auto-loads a session or the full list on mount.
 */
export function useSession({ autoLoad = false, sessionId = null } = {}) {
  const store = useSessionStore()

  onMounted(async () => {
    if (!autoLoad) return
    if (sessionId) {
      await store.loadSession(sessionId)
    } else {
      await store.fetchSessions()
    }
  })

  async function startSession({ name, scenarioId, scenarioName, projectId, metadata } = {}) {
    return store.createSession({
      name: name || 'Untitled Session',
      scenario_id: scenarioId,
      scenario_name: scenarioName,
      project_id: projectId,
      metadata,
    })
  }

  async function completeSession(id) {
    const target = id || store.activeSessionId
    if (!target) return null
    return store.updateSession(target, { status: 'completed' })
  }

  async function pauseSession(id) {
    const target = id || store.activeSessionId
    if (!target) return null
    return store.updateSession(target, { status: 'paused' })
  }

  async function resumeSession(id) {
    const target = id || store.activeSessionId
    if (!target) return null
    return store.updateSession(target, { status: 'active' })
  }

  async function archiveSession(id) {
    const target = id || store.activeSessionId
    if (!target) return null
    return store.updateSession(target, { status: 'archived' })
  }

  return {
    sessions: store.sessions,
    activeSession: store.activeSession,
    loading: store.loading,
    error: store.error,
    hasSessions: store.hasSessions,

    fetchSessions: store.fetchSessions,
    loadSession: store.loadSession,
    startSession,
    completeSession,
    pauseSession,
    resumeSession,
    archiveSession,
    deleteSession: store.deleteSession,
    addSimulation: store.addSimulation,
    setActiveSession: store.setActiveSession,
    clearActiveSession: store.clearActiveSession,
  }
}
