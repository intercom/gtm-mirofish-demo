import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/sessions', () => ({
  sessionsApi: {
    list: vi.fn(),
    create: vi.fn(),
    get: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    addSimulation: vi.fn(),
  },
}))

import { useSessionStore } from '../session'
import { sessionsApi } from '../../api/sessions'

describe('useSessionStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initialises with empty state', () => {
    const store = useSessionStore()
    expect(store.sessions).toEqual([])
    expect(store.activeSession).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- Computed ---

  it('activeSessionId is null when no active session', () => {
    const store = useSessionStore()
    expect(store.activeSessionId).toBeNull()
  })

  it('activeSessionId returns session_id of active session', () => {
    const store = useSessionStore()
    store.activeSession = { session_id: 'sess-1', name: 'Test' }
    expect(store.activeSessionId).toBe('sess-1')
  })

  it('hasSessions is false when empty', () => {
    const store = useSessionStore()
    expect(store.hasSessions).toBe(false)
  })

  it('hasSessions is true when sessions exist', () => {
    const store = useSessionStore()
    store.sessions = [{ session_id: 'sess-1' }]
    expect(store.hasSessions).toBe(true)
  })

  // --- fetchSessions ---

  it('fetchSessions populates sessions on success', async () => {
    const mockSessions = [
      { session_id: 'sess-1', name: 'Session 1' },
      { session_id: 'sess-2', name: 'Session 2' },
    ]
    sessionsApi.list.mockResolvedValue({ data: { sessions: mockSessions } })

    const store = useSessionStore()
    const result = await store.fetchSessions()

    expect(sessionsApi.list).toHaveBeenCalledWith({})
    expect(result).toEqual(mockSessions)
    expect(store.sessions).toEqual(mockSessions)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchSessions passes params to API', async () => {
    sessionsApi.list.mockResolvedValue({ data: { sessions: [] } })

    const store = useSessionStore()
    await store.fetchSessions({ limit: 10 })

    expect(sessionsApi.list).toHaveBeenCalledWith({ limit: 10 })
  })

  it('fetchSessions sets error and returns empty array on failure', async () => {
    sessionsApi.list.mockRejectedValue(new Error('Network error'))

    const store = useSessionStore()
    const result = await store.fetchSessions()

    expect(result).toEqual([])
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })

  // --- createSession ---

  it('createSession prepends to sessions and sets active', async () => {
    const newSession = { session_id: 'sess-new', name: 'New Session' }
    sessionsApi.create.mockResolvedValue({ data: newSession })

    const store = useSessionStore()
    store.sessions = [{ session_id: 'sess-old' }]
    const result = await store.createSession({ name: 'New Session' })

    expect(result).toEqual(newSession)
    expect(store.sessions[0]).toEqual(newSession)
    expect(store.sessions).toHaveLength(2)
    expect(store.activeSession).toEqual(newSession)
    expect(store.error).toBeNull()
  })

  it('createSession sets error and returns null on failure', async () => {
    sessionsApi.create.mockRejectedValue(new Error('Create failed'))

    const store = useSessionStore()
    const result = await store.createSession({ name: 'Test' })

    expect(result).toBeNull()
    expect(store.error).toBe('Create failed')
  })

  // --- loadSession ---

  it('loadSession sets activeSession and updates list entry', async () => {
    const sessionData = { session_id: 'sess-1', name: 'Updated Name' }
    sessionsApi.get.mockResolvedValue({ data: sessionData })

    const store = useSessionStore()
    store.sessions = [{ session_id: 'sess-1', name: 'Old Name' }]
    const result = await store.loadSession('sess-1')

    expect(result).toEqual(sessionData)
    expect(store.activeSession).toEqual(sessionData)
    expect(store.sessions[0]).toEqual(sessionData)
    expect(store.loading).toBe(false)
  })

  it('loadSession sets activeSession even if not in list', async () => {
    const sessionData = { session_id: 'sess-99', name: 'Not in list' }
    sessionsApi.get.mockResolvedValue({ data: sessionData })

    const store = useSessionStore()
    store.sessions = [{ session_id: 'sess-1' }]
    await store.loadSession('sess-99')

    expect(store.activeSession).toEqual(sessionData)
    expect(store.sessions).toHaveLength(1)
    expect(store.sessions[0].session_id).toBe('sess-1')
  })

  it('loadSession sets error on failure', async () => {
    sessionsApi.get.mockRejectedValue(new Error('Not found'))

    const store = useSessionStore()
    const result = await store.loadSession('sess-missing')

    expect(result).toBeNull()
    expect(store.error).toBe('Not found')
    expect(store.loading).toBe(false)
  })

  // --- updateSession ---

  it('updateSession updates active session if matching', async () => {
    const updated = { session_id: 'sess-1', name: 'Renamed' }
    sessionsApi.update.mockResolvedValue({ data: updated })

    const store = useSessionStore()
    store.activeSession = { session_id: 'sess-1', name: 'Original' }
    store.sessions = [{ session_id: 'sess-1', name: 'Original' }]
    const result = await store.updateSession('sess-1', { name: 'Renamed' })

    expect(result).toEqual(updated)
    expect(store.activeSession).toEqual(updated)
    expect(store.sessions[0]).toEqual(updated)
  })

  it('updateSession does not touch active session if ids differ', async () => {
    const updated = { session_id: 'sess-2', name: 'Other' }
    sessionsApi.update.mockResolvedValue({ data: updated })

    const store = useSessionStore()
    store.activeSession = { session_id: 'sess-1', name: 'Active' }
    store.sessions = [
      { session_id: 'sess-1', name: 'Active' },
      { session_id: 'sess-2', name: 'Old' },
    ]
    await store.updateSession('sess-2', { name: 'Other' })

    expect(store.activeSession.session_id).toBe('sess-1')
    expect(store.activeSession.name).toBe('Active')
    expect(store.sessions[1]).toEqual(updated)
  })

  it('updateSession sets error on failure', async () => {
    sessionsApi.update.mockRejectedValue(new Error('Update failed'))

    const store = useSessionStore()
    const result = await store.updateSession('sess-1', {})

    expect(result).toBeNull()
    expect(store.error).toBe('Update failed')
  })

  // --- deleteSession ---

  it('deleteSession removes from list and clears active if matching', async () => {
    sessionsApi.delete.mockResolvedValue({})

    const store = useSessionStore()
    store.activeSession = { session_id: 'sess-1' }
    store.sessions = [{ session_id: 'sess-1' }, { session_id: 'sess-2' }]
    const result = await store.deleteSession('sess-1')

    expect(result).toBe(true)
    expect(store.sessions).toHaveLength(1)
    expect(store.sessions[0].session_id).toBe('sess-2')
    expect(store.activeSession).toBeNull()
  })

  it('deleteSession does not clear active if ids differ', async () => {
    sessionsApi.delete.mockResolvedValue({})

    const store = useSessionStore()
    store.activeSession = { session_id: 'sess-1' }
    store.sessions = [{ session_id: 'sess-1' }, { session_id: 'sess-2' }]
    await store.deleteSession('sess-2')

    expect(store.activeSession.session_id).toBe('sess-1')
    expect(store.sessions).toHaveLength(1)
  })

  it('deleteSession sets error on failure', async () => {
    sessionsApi.delete.mockRejectedValue(new Error('Delete failed'))

    const store = useSessionStore()
    const result = await store.deleteSession('sess-1')

    expect(result).toBe(false)
    expect(store.error).toBe('Delete failed')
  })

  // --- setActiveSession / clearActiveSession ---

  it('setActiveSession assigns active session', () => {
    const store = useSessionStore()
    const session = { session_id: 'sess-1', name: 'Test' }
    store.setActiveSession(session)
    expect(store.activeSession).toEqual(session)
  })

  it('clearActiveSession nulls active session', () => {
    const store = useSessionStore()
    store.activeSession = { session_id: 'sess-1' }
    store.clearActiveSession()
    expect(store.activeSession).toBeNull()
  })

  // --- $reset ---

  it('$reset clears all state', () => {
    const store = useSessionStore()
    store.sessions = [{ session_id: 'sess-1' }]
    store.activeSession = { session_id: 'sess-1' }
    store.loading = true
    store.error = 'some error'

    store.$reset()

    expect(store.sessions).toEqual([])
    expect(store.activeSession).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })
})
