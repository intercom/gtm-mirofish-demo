import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useThemeStore } from '../theme'

describe('useThemeStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial activeThemeId is intercom', () => {
    const store = useThemeStore()
    expect(store.activeThemeId).toBe('intercom')
  })

  it('activeTheme computed resolves to the intercom theme object', () => {
    const store = useThemeStore()
    expect(store.activeTheme.id).toBe('intercom')
    expect(store.activeTheme.name).toBe('Intercom')
    expect(store.activeTheme.colors.primary).toBe('#2068FF')
  })

  it('themes contains all four default themes', () => {
    const store = useThemeStore()
    const ids = store.themes.map(t => t.id)
    expect(ids).toEqual(['intercom', 'dark', 'corporate', 'minimal'])
  })

  it('setTheme() changes activeThemeId for a valid id', () => {
    const store = useThemeStore()
    store.setTheme('dark')
    expect(store.activeThemeId).toBe('dark')
    expect(store.activeTheme.id).toBe('dark')
  })

  it('setTheme() ignores invalid theme ids', () => {
    const store = useThemeStore()
    store.setTheme('nonexistent')
    expect(store.activeThemeId).toBe('intercom')
  })

  it('resetTheme() reverts to intercom', () => {
    const store = useThemeStore()
    store.setTheme('dark')
    expect(store.activeThemeId).toBe('dark')
    store.resetTheme()
    expect(store.activeThemeId).toBe('intercom')
  })

  it('loads saved theme from localStorage on init', () => {
    localStorage.setItem('mirofish-theme-id', 'corporate')
    setActivePinia(createPinia())
    const store = useThemeStore()
    expect(store.activeThemeId).toBe('corporate')
  })

  it('ignores invalid theme id in localStorage', () => {
    localStorage.setItem('mirofish-theme-id', 'bogus')
    setActivePinia(createPinia())
    const store = useThemeStore()
    expect(store.activeThemeId).toBe('intercom')
  })

  it('handles corrupted localStorage gracefully', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage broken')
    })
    setActivePinia(createPinia())
    const store = useThemeStore()
    expect(store.activeThemeId).toBe('intercom')
  })

  it('themeToCSS() maps theme to CSS custom properties', () => {
    const store = useThemeStore()
    const css = store.themeToCSS(store.activeTheme)
    expect(css['--color-primary']).toBe('#2068FF')
    expect(css['--color-navy']).toBe('#050505')
    expect(css['--color-accent']).toBe('#AA00FF')
    expect(css['--color-bg']).toBe('#fafafa')
    expect(css['--color-surface']).toBe('#ffffff')
    expect(css['--color-text']).toBe('#050505')
    expect(css['--color-error']).toBe('#ef4444')
    expect(css['--color-success']).toBe('#009900')
    expect(css['--color-warning']).toBe('#f59e0b')
    expect(css['--font-family']).toBeDefined()
    expect(css['--font-heading']).toBeDefined()
    expect(css['--font-mono']).toBeDefined()
    expect(css['--radius-sm']).toBe('0.375rem')
    expect(css['--radius']).toBe('0.5rem')
    expect(css['--radius-lg']).toBe('0.75rem')
    expect(css['--shadow-sm']).toBeDefined()
    expect(css['--shadow-md']).toBeDefined()
    expect(css['--shadow-lg']).toBeDefined()
  })

  it('DEFAULT_THEMES is exposed and matches themes', () => {
    const store = useThemeStore()
    expect(store.DEFAULT_THEMES).toHaveLength(4)
    expect(store.DEFAULT_THEMES.map(t => t.id)).toEqual(['intercom', 'dark', 'corporate', 'minimal'])
  })
})
