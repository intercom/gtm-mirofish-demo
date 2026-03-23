import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useToastStore } from '../stores/toast.js'

describe('useToastStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  it('starts with no toasts', () => {
    const store = useToastStore()
    expect(store.toasts).toEqual([])
  })

  it('adds a toast via add()', () => {
    const store = useToastStore()
    store.add({ message: 'Hello', type: 'info' })
    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0].message).toBe('Hello')
    expect(store.toasts[0].type).toBe('info')
  })

  it('success() creates a success toast', () => {
    const store = useToastStore()
    store.success('Saved!')
    expect(store.toasts[0].type).toBe('success')
    expect(store.toasts[0].message).toBe('Saved!')
  })

  it('error() creates an error toast', () => {
    const store = useToastStore()
    store.error('Failed!')
    expect(store.toasts[0].type).toBe('error')
  })

  it('info() creates an info toast', () => {
    const store = useToastStore()
    store.info('FYI')
    expect(store.toasts[0].type).toBe('info')
  })

  it('removes a toast by id', () => {
    const store = useToastStore()
    const id = store.add({ message: 'temp', type: 'info', duration: 0 })
    expect(store.toasts).toHaveLength(1)
    store.remove(id)
    expect(store.toasts).toHaveLength(0)
  })

  it('auto-removes toast after duration', () => {
    const store = useToastStore()
    store.add({ message: 'auto', type: 'info', duration: 3000 })
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(3000)
    expect(store.toasts).toHaveLength(0)
  })

  it('does not auto-remove when duration is 0', () => {
    const store = useToastStore()
    store.add({ message: 'sticky', type: 'info', duration: 0 })
    vi.advanceTimersByTime(10000)
    expect(store.toasts).toHaveLength(1)
  })

  it('assigns unique ids to each toast', () => {
    const store = useToastStore()
    const id1 = store.add({ message: 'a', type: 'info', duration: 0 })
    const id2 = store.add({ message: 'b', type: 'info', duration: 0 })
    expect(id1).not.toBe(id2)
  })
})
