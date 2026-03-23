import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingsStore } from '../settings'

describe('settings store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('initializes with defaults when localStorage is empty', () => {
    const store = useSettingsStore()
    expect(store.provider).toBe('anthropic')
    expect(store.apiKey).toBe('')
    expect(store.zepKey).toBe('')
    expect(store.connectionStatus).toEqual({ llm: null, zep: null })
  })

  it('hydrates from localStorage on creation', () => {
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

  it('persists provider to localStorage', () => {
    const store = useSettingsStore()
    store.setProvider('gemini')
    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved.provider).toBe('gemini')
  })

  it('persists apiKey to localStorage', () => {
    const store = useSettingsStore()
    store.setApiKey('sk-new')
    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved.apiKey).toBe('sk-new')
  })

  it('persists zepKey to localStorage', () => {
    const store = useSettingsStore()
    store.setZepKey('zep-new')
    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved.zepKey).toBe('zep-new')
  })

  it('provides currentProvider computed', () => {
    const store = useSettingsStore()
    expect(store.currentProvider.id).toBe('anthropic')
    store.setProvider('openai')
    expect(store.currentProvider.id).toBe('openai')
  })

  it('sets connection status', () => {
    const store = useSettingsStore()
    store.setConnectionStatus('llm', 'testing')
    expect(store.connectionStatus.llm).toBe('testing')
    store.setConnectionStatus('zep', 'success')
    expect(store.connectionStatus.zep).toBe('success')
  })

  it('exposes providers list', () => {
    const store = useSettingsStore()
    expect(store.providers).toHaveLength(3)
    expect(store.providers.map((p) => p.id)).toEqual(['anthropic', 'openai', 'gemini'])
  })

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem('mirofish-settings', 'not-json')
    setActivePinia(createPinia())
    const store = useSettingsStore()
    expect(store.provider).toBe('anthropic')
  })
})
