import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish-theme-id'

/**
 * Theme shape:
 * {
 *   id: string,
 *   name: string,
 *   colors: { primary, secondary, accent, background, surface, text, error, success, warning },
 *   fonts:  { heading, body, mono },
 *   borderRadius: { sm, md, lg },
 *   shadows: { sm, md, lg },
 * }
 */

const SYSTEM_FONTS = 'system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"'
const MONO_FONTS = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

const DEFAULT_THEMES = [
  {
    id: 'intercom',
    name: 'Intercom',
    colors: {
      primary: '#2068FF',
      secondary: '#050505',
      accent: '#AA00FF',
      background: '#fafafa',
      surface: '#ffffff',
      text: '#050505',
      error: '#ef4444',
      success: '#009900',
      warning: '#f59e0b',
    },
    fonts: {
      heading: SYSTEM_FONTS,
      body: SYSTEM_FONTS,
      mono: MONO_FONTS,
    },
    borderRadius: { sm: '0.375rem', md: '0.5rem', lg: '0.75rem' },
    shadows: {
      sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
      md: '0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06)',
      lg: '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
    },
  },
  {
    id: 'dark',
    name: 'Dark',
    colors: {
      primary: '#2068FF',
      secondary: '#1a1a3e',
      accent: '#AA00FF',
      background: '#0a0a1a',
      surface: '#1a1a2e',
      text: '#e0e0e0',
      error: '#ef4444',
      success: '#4ade80',
      warning: '#fbbf24',
    },
    fonts: {
      heading: SYSTEM_FONTS,
      body: SYSTEM_FONTS,
      mono: MONO_FONTS,
    },
    borderRadius: { sm: '0.375rem', md: '0.5rem', lg: '0.75rem' },
    shadows: {
      sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
      md: '0 4px 6px rgba(0, 0, 0, 0.35), 0 2px 4px rgba(0, 0, 0, 0.3)',
      lg: '0 10px 15px rgba(0, 0, 0, 0.4), 0 4px 6px rgba(0, 0, 0, 0.3)',
    },
  },
  {
    id: 'corporate',
    name: 'Corporate',
    colors: {
      primary: '#1a365d',
      secondary: '#2d3748',
      accent: '#2b6cb0',
      background: '#f7fafc',
      surface: '#ffffff',
      text: '#1a202c',
      error: '#c53030',
      success: '#276749',
      warning: '#c05621',
    },
    fonts: {
      heading: 'Georgia, "Times New Roman", Times, serif',
      body: SYSTEM_FONTS,
      mono: MONO_FONTS,
    },
    borderRadius: { sm: '0.25rem', md: '0.375rem', lg: '0.5rem' },
    shadows: {
      sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
      md: '0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06)',
      lg: '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
    },
  },
  {
    id: 'minimal',
    name: 'Minimal',
    colors: {
      primary: '#525252',
      secondary: '#737373',
      accent: '#404040',
      background: '#fafafa',
      surface: '#ffffff',
      text: '#171717',
      error: '#dc2626',
      success: '#16a34a',
      warning: '#d97706',
    },
    fonts: {
      heading: SYSTEM_FONTS,
      body: SYSTEM_FONTS,
      mono: MONO_FONTS,
    },
    borderRadius: { sm: '0.25rem', md: '0.25rem', lg: '0.375rem' },
    shadows: {
      sm: 'none',
      md: 'none',
      lg: '0 1px 2px rgba(0, 0, 0, 0.05)',
    },
  },
]

// Map theme object properties → CSS custom property names
function themeToCSS(theme) {
  return {
    '--color-primary': theme.colors.primary,
    '--color-navy': theme.colors.secondary,
    '--color-accent': theme.colors.accent,
    '--color-bg': theme.colors.background,
    '--color-surface': theme.colors.surface,
    '--color-text': theme.colors.text,
    '--color-error': theme.colors.error,
    '--color-success': theme.colors.success,
    '--color-warning': theme.colors.warning,
    '--font-family': theme.fonts.body,
    '--font-heading': theme.fonts.heading,
    '--font-mono': theme.fonts.mono,
    '--radius-sm': theme.borderRadius.sm,
    '--radius': theme.borderRadius.md,
    '--radius-lg': theme.borderRadius.lg,
    '--shadow-sm': theme.shadows.sm,
    '--shadow-md': theme.shadows.md,
    '--shadow-lg': theme.shadows.lg,
  }
}

function applyThemeToDOM(theme) {
  const vars = themeToCSS(theme)
  const root = document.documentElement
  for (const [prop, value] of Object.entries(vars)) {
    root.style.setProperty(prop, value)
  }
}

function clearThemeFromDOM() {
  const sampleTheme = DEFAULT_THEMES[0]
  const vars = themeToCSS(sampleTheme)
  const root = document.documentElement
  for (const prop of Object.keys(vars)) {
    root.style.removeProperty(prop)
  }
}

export const useThemeStore = defineStore('theme', () => {
  const activeThemeId = ref('intercom')
  const themes = ref([...DEFAULT_THEMES])

  const activeTheme = computed(() =>
    themes.value.find((t) => t.id === activeThemeId.value) || themes.value[0],
  )

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved && themes.value.some((t) => t.id === saved)) {
        activeThemeId.value = saved
      }
    } catch {
      // Corrupted data — keep default
    }
  }

  function setTheme(id) {
    if (!themes.value.some((t) => t.id === id)) return
    activeThemeId.value = id
  }

  function resetTheme() {
    activeThemeId.value = 'intercom'
    clearThemeFromDOM()
  }

  // Persist selection and apply CSS vars on change
  watch(activeTheme, (theme) => {
    localStorage.setItem(STORAGE_KEY, theme.id)
    if (theme.id === 'intercom') {
      clearThemeFromDOM()
    } else {
      applyThemeToDOM(theme)
    }
  }, { flush: 'post' })

  // Initialize
  load()
  if (activeThemeId.value !== 'intercom') {
    applyThemeToDOM(activeTheme.value)
  }

  return {
    activeThemeId,
    activeTheme,
    themes,
    setTheme,
    resetTheme,
    themeToCSS,
    DEFAULT_THEMES,
  }
})
