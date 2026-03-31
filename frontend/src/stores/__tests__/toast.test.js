import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useToastStore } from '../toast'

describe('useToastStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('initialises with empty toasts', () => {
    const store = useToastStore()
    expect(store.toasts).toEqual([])
  })

  it('add() creates a toast with default type info', () => {
    const store = useToastStore()
    store.add({ message: 'Hello' })
    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0].message).toBe('Hello')
    expect(store.toasts[0].type).toBe('info')
  })

  it('add() returns the toast id', () => {
    const store = useToastStore()
    const id = store.add({ message: 'Test' })
    expect(typeof id).toBe('number')
    expect(store.toasts[0].id).toBe(id)
  })

  it('add() assigns incrementing ids', () => {
    const store = useToastStore()
    const id1 = store.add({ message: 'First' })
    const id2 = store.add({ message: 'Second' })
    expect(id2).toBeGreaterThan(id1)
  })

  it('remove() removes a toast by id', () => {
    const store = useToastStore()
    const id = store.add({ message: 'Remove me', duration: 0 })
    expect(store.toasts).toHaveLength(1)
    store.remove(id)
    expect(store.toasts).toHaveLength(0)
  })

  it('remove() only removes the targeted toast', () => {
    const store = useToastStore()
    store.add({ message: 'Keep', duration: 0 })
    const removeId = store.add({ message: 'Remove', duration: 0 })
    store.add({ message: 'Also keep', duration: 0 })
    store.remove(removeId)
    expect(store.toasts).toHaveLength(2)
    expect(store.toasts.map(t => t.message)).toEqual(['Keep', 'Also keep'])
  })

  it('success() creates toast with type success', () => {
    const store = useToastStore()
    store.success('Saved!')
    expect(store.toasts[0].type).toBe('success')
    expect(store.toasts[0].message).toBe('Saved!')
  })

  it('error() creates toast with type error', () => {
    const store = useToastStore()
    store.error('Something broke')
    expect(store.toasts[0].type).toBe('error')
    expect(store.toasts[0].message).toBe('Something broke')
  })

  it('info() creates toast with type info', () => {
    const store = useToastStore()
    store.info('FYI')
    expect(store.toasts[0].type).toBe('info')
    expect(store.toasts[0].message).toBe('FYI')
  })

  it('auto-removes toast after default duration (4s)', () => {
    const store = useToastStore()
    store.add({ message: 'Temporary' })
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(4000)
    expect(store.toasts).toHaveLength(0)
  })

  it('error() auto-removes after 6s', () => {
    const store = useToastStore()
    store.error('Longer error')
    vi.advanceTimersByTime(4000)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(2000)
    expect(store.toasts).toHaveLength(0)
  })

  it('duration 0 disables auto-remove', () => {
    const store = useToastStore()
    store.add({ message: 'Sticky', duration: 0 })
    vi.advanceTimersByTime(60000)
    expect(store.toasts).toHaveLength(1)
  })

  it('custom duration auto-removes at correct time', () => {
    const store = useToastStore()
    store.add({ message: 'Custom', duration: 2000 })
    vi.advanceTimersByTime(1999)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(store.toasts).toHaveLength(0)
  })
})
