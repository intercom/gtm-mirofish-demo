import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNotificationStore } from '../notifications'

describe('useNotificationStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  // --- Initial state ---

  it('has empty initial state', () => {
    const store = useNotificationStore()
    expect(store.notifications).toEqual([])
    expect(store.unreadCount).toBe(0)
  })

  // --- add ---

  it('add creates a notification with default type info', () => {
    const store = useNotificationStore()
    const id = store.add({ title: 'Hello' })
    expect(typeof id).toBe('number')
    expect(store.notifications).toHaveLength(1)
    expect(store.notifications[0].title).toBe('Hello')
    expect(store.notifications[0].type).toBe('info')
    expect(store.notifications[0].message).toBe('')
    expect(store.notifications[0].read).toBe(false)
    expect(store.notifications[0].timestamp).toBeGreaterThan(0)
  })

  it('add returns the notification id', () => {
    const store = useNotificationStore()
    const id1 = store.add({ title: 'First' })
    const id2 = store.add({ title: 'Second' })
    expect(id2).toBeGreaterThan(id1)
  })

  it('add prepends new notifications (unshift)', () => {
    const store = useNotificationStore()
    store.add({ title: 'First' })
    store.add({ title: 'Second' })
    expect(store.notifications[0].title).toBe('Second')
    expect(store.notifications[1].title).toBe('First')
  })

  it('add accepts custom type and message', () => {
    const store = useNotificationStore()
    store.add({ title: 'Error occurred', message: 'Details here', type: 'error' })
    expect(store.notifications[0].type).toBe('error')
    expect(store.notifications[0].message).toBe('Details here')
  })

  // --- unreadCount computed ---

  it('unreadCount reflects unread notifications', () => {
    const store = useNotificationStore()
    store.add({ title: 'A' })
    store.add({ title: 'B' })
    store.add({ title: 'C' })
    expect(store.unreadCount).toBe(3)
  })

  it('unreadCount decreases when notifications are marked read', () => {
    const store = useNotificationStore()
    const id = store.add({ title: 'A' })
    store.add({ title: 'B' })
    store.markRead(id)
    expect(store.unreadCount).toBe(1)
  })

  // --- markRead ---

  it('markRead marks a single notification as read', () => {
    const store = useNotificationStore()
    const id = store.add({ title: 'Test' })
    store.markRead(id)
    expect(store.notifications[0].read).toBe(true)
  })

  it('markRead is no-op for non-existent id', () => {
    const store = useNotificationStore()
    store.add({ title: 'Test' })
    store.markRead(9999)
    expect(store.notifications[0].read).toBe(false)
  })

  // --- markAllRead ---

  it('markAllRead marks all notifications as read', () => {
    const store = useNotificationStore()
    store.add({ title: 'A' })
    store.add({ title: 'B' })
    store.add({ title: 'C' })
    store.markAllRead()
    expect(store.unreadCount).toBe(0)
    expect(store.notifications.every(n => n.read)).toBe(true)
  })

  // --- remove ---

  it('remove deletes notification by id', () => {
    const store = useNotificationStore()
    const id1 = store.add({ title: 'A' })
    store.add({ title: 'B' })
    store.remove(id1)
    expect(store.notifications).toHaveLength(1)
    expect(store.notifications[0].title).toBe('B')
  })

  it('remove is no-op for non-existent id', () => {
    const store = useNotificationStore()
    store.add({ title: 'A' })
    store.remove(9999)
    expect(store.notifications).toHaveLength(1)
  })

  // --- clear ---

  it('clear empties all notifications', () => {
    const store = useNotificationStore()
    store.add({ title: 'A' })
    store.add({ title: 'B' })
    store.clear()
    expect(store.notifications).toEqual([])
    expect(store.unreadCount).toBe(0)
  })
})
