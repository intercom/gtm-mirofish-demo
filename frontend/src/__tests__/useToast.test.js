import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useToast } from '../composables/useToast'

describe('useToast', () => {
  beforeEach(() => {
    const { toasts } = useToast()
    toasts.value = []
  })

  it('adds a success toast', () => {
    const { success, toasts } = useToast()
    success('Operation completed')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('success')
    expect(toasts.value[0].message).toBe('Operation completed')
  })

  it('adds an error toast', () => {
    const { error, toasts } = useToast()
    error('Something failed')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('error')
    expect(toasts.value[0].message).toBe('Something failed')
  })

  it('adds an info toast', () => {
    const { info, toasts } = useToast()
    info('FYI')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('info')
  })

  it('removes a toast by id', () => {
    const { success, toasts, removeToast } = useToast()
    success('One')
    success('Two')
    expect(toasts.value).toHaveLength(2)
    removeToast(toasts.value[0].id)
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Two')
  })

  it('auto-removes toast after duration', async () => {
    vi.useFakeTimers()
    const { success, toasts } = useToast()
    success('Temporary', 2000)
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(2000)
    expect(toasts.value).toHaveLength(0)
    vi.useRealTimers()
  })

  it('shares state across calls (singleton)', () => {
    const a = useToast()
    const b = useToast()
    a.success('Shared')
    expect(b.toasts.value).toHaveLength(1)
  })
})
