import { describe, it, expect, beforeEach, vi } from 'vitest'
import { resolveTheme, applyClass, STORAGE_KEY, DARK_ROUTES } from '../useTheme.js'

describe('resolveTheme', () => {
  beforeEach(() => {
    // Reset matchMedia mock between tests
    vi.stubGlobal('matchMedia', vi.fn((query) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })))
  })

  it('returns "dark" when preference is "dark"', () => {
    expect(resolveTheme('dark', 'landing')).toBe('dark')
    expect(resolveTheme('dark', 'settings')).toBe('dark')
  })

  it('returns "light" when preference is "light"', () => {
    expect(resolveTheme('light', 'landing')).toBe('light')
    expect(resolveTheme('light', 'settings')).toBe('light')
  })

  it('follows system preference when set to "system"', () => {
    // System prefers light
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })))
    expect(resolveTheme('system', 'landing')).toBe('light')

    // System prefers dark
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })))
    expect(resolveTheme('system', 'settings')).toBe('dark')
  })

  it('defaults to dark on landing route when "auto"', () => {
    expect(resolveTheme('auto', 'landing')).toBe('dark')
  })

  it('defaults to dark on login route when "auto"', () => {
    expect(resolveTheme('auto', 'login')).toBe('dark')
  })

  it('defaults to light on app routes when "auto"', () => {
    expect(resolveTheme('auto', 'settings')).toBe('light')
    expect(resolveTheme('auto', 'scenario-builder')).toBe('light')
    expect(resolveTheme('auto', 'simulation')).toBe('light')
    expect(resolveTheme('auto', 'report')).toBe('light')
    expect(resolveTheme('auto', 'chat')).toBe('light')
    expect(resolveTheme('auto', 'graph')).toBe('light')
  })
})

describe('applyClass', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark')
  })

  it('adds "dark" class when isDark is true', () => {
    applyClass(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('removes "dark" class when isDark is false', () => {
    document.documentElement.classList.add('dark')
    applyClass(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})

describe('DARK_ROUTES', () => {
  it('contains landing and login', () => {
    expect(DARK_ROUTES.has('landing')).toBe(true)
    expect(DARK_ROUTES.has('login')).toBe(true)
  })

  it('does not contain app routes', () => {
    expect(DARK_ROUTES.has('settings')).toBe(false)
    expect(DARK_ROUTES.has('simulation')).toBe(false)
  })
})

describe('localStorage persistence', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('reads preference from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'dark')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })

  it('defaults to null when no preference stored', () => {
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
  })

  it('uses correct storage key', () => {
    expect(STORAGE_KEY).toBe('mirofish-theme')
  })
})
