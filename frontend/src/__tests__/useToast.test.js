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

  it('adds a warning toast', () => {
    const { warning, toasts } = useToast()
    warning('Be careful')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('warning')
    expect(toasts.value[0].message).toBe('Be careful')
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
    success('Temporary', { duration: 2000 })
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

  it('returns toast id from helper methods', () => {
    const { success, error, info, warning } = useToast()
    expect(typeof success('a')).toBe('number')
    expect(typeof error('b')).toBe('number')
    expect(typeof info('c')).toBe('number')
    expect(typeof warning('d')).toBe('number')
  })

  it('clears all toasts', () => {
    const { success, error, toasts, clearAll } = useToast()
    success('One')
    error('Two')
    expect(toasts.value).toHaveLength(2)
    clearAll()
    expect(toasts.value).toHaveLength(0)
  })

  it('caps toasts at 5, removing oldest first', () => {
    const { info, toasts } = useToast()
    for (let i = 0; i < 7; i++) {
      info(`Toast ${i}`)
    }
    expect(toasts.value).toHaveLength(5)
    expect(toasts.value[0].message).toBe('Toast 2')
    expect(toasts.value[4].message).toBe('Toast 6')
  })

  it('stores duration and createdAt on each toast', () => {
    const { info, toasts } = useToast()
    info('Timed')
    expect(toasts.value[0].duration).toBe(4000)
    expect(typeof toasts.value[0].createdAt).toBe('number')
  })

  it('supports action on toast', () => {
    const onClick = vi.fn()
    const { success, toasts } = useToast()
    success('Done', { action: { label: 'Undo', onClick } })
    expect(toasts.value[0].action).toEqual({ label: 'Undo', onClick })
  })

  it('uses type-specific default durations', () => {
    vi.useFakeTimers()
    const { error, toasts } = useToast()
    error('Fail')
    expect(toasts.value[0].duration).toBe(6000)
    vi.advanceTimersByTime(6000)
    expect(toasts.value).toHaveLength(0)
    vi.useRealTimers()
  })
})
