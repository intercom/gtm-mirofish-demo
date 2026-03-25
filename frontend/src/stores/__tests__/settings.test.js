import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '../settings'

describe('useSettingsStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('initialises with default values', () => {
    const store = useSettingsStore()
    expect(store.provider).toBe('anthropic')
    expect(store.apiKey).toBe('')
    expect(store.zepKey).toBe('')
    expect(store.connectionStatus).toEqual({ llm: null, zep: null })
  })

  it('loads settings from localStorage', () => {
    localStorage.setItem('mirofish-settings', JSON.stringify({
      provider: 'openai',
      apiKey: 'sk-test',
      zepKey: 'zep-test',
    }))
    setActivePinia(createPinia())
    const store = useSettingsStore()
    expect(store.provider).toBe('openai')
    expect(store.apiKey).toBe('sk-test')
    expect(store.zepKey).toBe('zep-test')
  })

  it('persists to localStorage on save()', () => {
    const store = useSettingsStore()
    store.provider = 'gemini'
    store.apiKey = 'key-123'
    store.save()

    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved.provider).toBe('gemini')
    expect(saved.apiKey).toBe('key-123')
  })

  it('exposes providers list', () => {
    const store = useSettingsStore()
    expect(store.providers).toHaveLength(3)
    expect(store.providers.map(p => p.id)).toEqual(['anthropic', 'openai', 'gemini'])
  })

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem('mirofish-settings', 'not-json')
    setActivePinia(createPinia())
    const store = useSettingsStore()
    expect(store.provider).toBe('anthropic')
  })

  it('testConnection sets status to error on network failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network')))
    const store = useSettingsStore()
    await store.testConnection('llm')
    expect(store.connectionStatus.llm).toBe('error')
    vi.unstubAllGlobals()
  })

  it('testConnection sets status to success on 200', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }))
    const store = useSettingsStore()
    await store.testConnection('zep')
    expect(store.connectionStatus.zep).toBe('success')
    vi.unstubAllGlobals()
  })

  it('testConnection sets intermediate testing status', async () => {
    let resolvePromise
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() =>
      new Promise(resolve => { resolvePromise = resolve })
    ))
    const store = useSettingsStore()
    const promise = store.testConnection('llm')
    expect(store.connectionStatus.llm).toBe('testing')
    resolvePromise({ ok: true })
    await promise
    expect(store.connectionStatus.llm).toBe('success')
    vi.unstubAllGlobals()
  })

  it('testConnection sets error on non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }))
    const store = useSettingsStore()
    await store.testConnection('llm')
    expect(store.connectionStatus.llm).toBe('error')
    vi.unstubAllGlobals()
  })
})
