import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import { useLocaleStore } from '../locale'

describe('useLocaleStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  it('defaults to en-US when no localStorage or browser locale', () => {
    vi.spyOn(navigator, 'language', 'get').mockReturnValue(undefined)
    vi.spyOn(navigator, 'languages', 'get').mockReturnValue(undefined)
    setActivePinia(createPinia())
    const store = useLocaleStore()
    expect(store.locale).toBe('en-US')
  })

  it('setLocale() changes locale for a valid code', () => {
    const store = useLocaleStore()
    store.setLocale('de-DE')
    expect(store.locale).toBe('de-DE')
  })

  it('setLocale() ignores invalid locale codes', () => {
    const store = useLocaleStore()
    store.setLocale('xx-YY')
    expect(store.locale).not.toBe('xx-YY')
  })

  it('supportedLocales contains expected entries', () => {
    const store = useLocaleStore()
    const codes = store.supportedLocales.map(l => l.code)
    expect(codes).toContain('en-US')
    expect(codes).toContain('en-GB')
    expect(codes).toContain('de-DE')
    expect(codes).toContain('fr-FR')
    expect(codes).toContain('ja-JP')
    expect(codes).toContain('zh-CN')
    expect(codes).toContain('pt-BR')
    expect(codes).toContain('es-ES')
  })

  it('each supported locale has code and label', () => {
    const store = useLocaleStore()
    for (const loc of store.supportedLocales) {
      expect(loc.code).toBeTruthy()
      expect(loc.label).toBeTruthy()
    }
  })

  it('persists locale to localStorage on change', async () => {
    const store = useLocaleStore()
    store.setLocale('fr-FR')
    await nextTick()
    expect(localStorage.getItem('mirofish-locale')).toBe('fr-FR')
  })

  it('loads saved locale from localStorage on init', () => {
    localStorage.setItem('mirofish-locale', 'ja-JP')
    setActivePinia(createPinia())
    const store = useLocaleStore()
    expect(store.locale).toBe('ja-JP')
  })

  it('falls back to browser locale detection if no localStorage', () => {
    vi.spyOn(navigator, 'language', 'get').mockReturnValue('de-DE')
    setActivePinia(createPinia())
    const store = useLocaleStore()
    expect(store.locale).toBe('de-DE')
  })

  it('falls back to prefix match for browser locale', () => {
    vi.spyOn(navigator, 'language', 'get').mockReturnValue('de')
    setActivePinia(createPinia())
    const store = useLocaleStore()
    expect(store.locale).toBe('de-DE')
  })

  it('ignores invalid localStorage value and uses browser locale', () => {
    localStorage.setItem('mirofish-locale', 'invalid-code')
    vi.spyOn(navigator, 'language', 'get').mockReturnValue('fr-FR')
    setActivePinia(createPinia())
    const store = useLocaleStore()
    expect(store.locale).toBe('fr-FR')
  })
})
