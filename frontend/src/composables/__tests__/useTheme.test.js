import { describe, it, expect, beforeEach, vi } from 'vitest'

// The useTheme composable uses module-level state that persists across calls,
// so we need to reset modules for isolation.
let useTheme

describe('useTheme', () => {
  beforeEach(async () => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')

    vi.stubGlobal('matchMedia', vi.fn((query) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })))

    // Reset the module to clear the `initialized` flag
    vi.resetModules()
    const mod = await import('../useTheme.js')
    useTheme = mod.useTheme
  })

  it('returns preference, isDark, setTheme, and setRouteDefault', () => {
    const result = useTheme()
    expect(result).toHaveProperty('preference')
    expect(result).toHaveProperty('isDark')
    expect(result).toHaveProperty('setTheme')
    expect(result).toHaveProperty('setRouteDefault')
  })

  it('defaults preference to "system"', () => {
    const { preference } = useTheme()
    expect(preference.value).toBe('system')
  })

  it('isDark is false when system prefers light and preference is system', () => {
    const { isDark } = useTheme()
    expect(isDark.value).toBe(false)
  })

  it('isDark is true when preference is "dark"', () => {
    const { isDark, setTheme } = useTheme()
    setTheme('dark')
    expect(isDark.value).toBe(true)
  })

  it('isDark is false when preference is "light"', () => {
    const { isDark, setTheme } = useTheme()
    setTheme('light')
    expect(isDark.value).toBe(false)
  })

  it('follows system preference when set to "system" and system is dark', async () => {
    vi.resetModules()

    vi.stubGlobal('matchMedia', vi.fn((query) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })))

    const mod = await import('../useTheme.js')
    const { isDark } = mod.useTheme()
    expect(isDark.value).toBe(true)
  })

  it('persists preference to localStorage via setTheme', () => {
    const { setTheme } = useTheme()
    setTheme('dark')
    expect(localStorage.getItem('mirofish-theme')).toBe('dark')
  })

  it('reads preference from localStorage on init', async () => {
    localStorage.setItem('mirofish-theme', 'dark')

    vi.resetModules()
    vi.stubGlobal('matchMedia', vi.fn((query) => ({
      matches: false,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })))

    const mod = await import('../useTheme.js')
    const { preference } = mod.useTheme()
    expect(preference.value).toBe('dark')
  })

  it('ignores invalid theme values in setTheme', () => {
    const { preference, setTheme } = useTheme()
    setTheme('invalid-theme')
    expect(preference.value).toBe('system')
  })

  it('applies dark class to documentElement when isDark is true', () => {
    const { setTheme } = useTheme()
    setTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('removes dark class when isDark becomes false', () => {
    const { setTheme } = useTheme()
    setTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    setTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('uses correct storage key "mirofish-theme"', () => {
    const { setTheme } = useTheme()
    setTheme('light')
    expect(localStorage.getItem('mirofish-theme')).toBe('light')
  })
})
