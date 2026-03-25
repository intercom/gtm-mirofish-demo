import { describe, it, expect, beforeEach, vi } from 'vitest'

// Reset module state between tests by re-importing fresh
let useTheme

function createMockMatchMedia(matches = false) {
  const listeners = []
  const mql = {
    matches,
    addEventListener: vi.fn((_, cb) => listeners.push(cb)),
    removeEventListener: vi.fn(),
  }
  return { mql, listeners, mock: vi.fn(() => mql) }
}

beforeEach(async () => {
  localStorage.clear()
  document.documentElement.classList.remove('dark')

  // Reset module so `initialized` flag resets
  vi.resetModules()
  const mod = await import('./useTheme.js')
  useTheme = mod.useTheme
})

describe('useTheme', () => {
  it('defaults to system preference when no localStorage value', () => {
    const media = createMockMatchMedia(false)
    window.matchMedia = media.mock

    const { preference, isDark } = useTheme()
    expect(preference.value).toBe('system')
    expect(isDark.value).toBe(false)
  })

  it('applies dark class when system prefers dark', () => {
    const media = createMockMatchMedia(true)
    window.matchMedia = media.mock

    const { isDark } = useTheme()
    expect(isDark.value).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('reads preference from localStorage', () => {
    localStorage.setItem('mirofish-theme', 'dark')
    const media = createMockMatchMedia(false)
    window.matchMedia = media.mock

    const { preference, isDark } = useTheme()
    expect(preference.value).toBe('dark')
    expect(isDark.value).toBe(true)
  })

  it('persists preference to localStorage on setTheme', () => {
    const media = createMockMatchMedia(false)
    window.matchMedia = media.mock

    const { setTheme } = useTheme()
    setTheme('dark')
    expect(localStorage.getItem('mirofish-theme')).toBe('dark')
  })

  it('ignores invalid theme values', () => {
    const media = createMockMatchMedia(false)
    window.matchMedia = media.mock

    const { preference, setTheme } = useTheme()
    setTheme('invalid')
    expect(preference.value).toBe('system')
  })

  it('removes dark class when set to light', () => {
    const media = createMockMatchMedia(true)
    window.matchMedia = media.mock

    const { setTheme } = useTheme()
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    setTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('toggles dark class when switching between themes', () => {
    const media = createMockMatchMedia(false)
    window.matchMedia = media.mock

    const { setTheme } = useTheme()
    expect(document.documentElement.classList.contains('dark')).toBe(false)

    setTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    setTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('ignores invalid localStorage values', () => {
    localStorage.setItem('mirofish-theme', 'neon')
    const media = createMockMatchMedia(false)
    window.matchMedia = media.mock

    const { preference } = useTheme()
    expect(preference.value).toBe('system')
  })

  describe('systemPreference', () => {
    it('exposes system preference as light when OS prefers light', () => {
      const media = createMockMatchMedia(false)
      window.matchMedia = media.mock

      const { systemPreference } = useTheme()
      expect(systemPreference.value).toBe('light')
    })

    it('exposes system preference as dark when OS prefers dark', () => {
      const media = createMockMatchMedia(true)
      window.matchMedia = media.mock

      const { systemPreference } = useTheme()
      expect(systemPreference.value).toBe('dark')
    })

    it('updates systemPreference reactively when OS changes', async () => {
      const media = createMockMatchMedia(false)
      window.matchMedia = media.mock

      const { systemPreference } = useTheme()
      expect(systemPreference.value).toBe('light')

      media.listeners[0]({ matches: true })
      expect(systemPreference.value).toBe('dark')
    })
  })

  describe('route-aware defaults', () => {
    it('uses dark route default when no explicit preference is stored', () => {
      const media = createMockMatchMedia(false)
      window.matchMedia = media.mock

      const { isDark, setRouteDefault } = useTheme()
      expect(isDark.value).toBe(false)

      setRouteDefault('dark')
      expect(isDark.value).toBe(true)
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })

    it('uses light route default when no explicit preference is stored', () => {
      const media = createMockMatchMedia(true)
      window.matchMedia = media.mock

      const { isDark, setRouteDefault } = useTheme()
      expect(isDark.value).toBe(true)

      setRouteDefault('light')
      expect(isDark.value).toBe(false)
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })

    it('ignores route default when user has explicitly set a preference', () => {
      localStorage.setItem('mirofish-theme', 'light')
      const media = createMockMatchMedia(false)
      window.matchMedia = media.mock

      const { isDark, setRouteDefault } = useTheme()
      setRouteDefault('dark')
      expect(isDark.value).toBe(false)
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })

    it('ignores route default after setTheme is called', () => {
      const media = createMockMatchMedia(false)
      window.matchMedia = media.mock

      const { isDark, setTheme, setRouteDefault } = useTheme()
      setRouteDefault('dark')
      expect(isDark.value).toBe(true)

      setTheme('light')
      setRouteDefault('dark')
      expect(isDark.value).toBe(false)
    })
  })
})
