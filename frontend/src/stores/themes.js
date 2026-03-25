import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish-custom-themes'

const DEFAULT_THEME_PROPS = {
  '--color-primary': '#2068FF',
  '--color-accent': '#AA00FF',
  '--color-fin-orange': '#ff5600',
  '--color-bg': '#fafafa',
  '--color-surface': '#ffffff',
  '--color-text': '#050505',
  '--color-text-secondary': '#555555',
  '--font-family': 'system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  '--font-mono': 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
  '--radius-sm': '0.375rem',
  '--radius': '0.5rem',
  '--radius-lg': '0.75rem',
  '--radius-xl': '1rem',
  '--shadow-intensity': '1',
}

const FONT_OPTIONS = [
  { value: 'system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif', label: 'System Default' },
  { value: '"Inter", system-ui, sans-serif', label: 'Inter' },
  { value: '"Georgia", serif', label: 'Georgia' },
  { value: '"Courier New", monospace', label: 'Courier New' },
  { value: '"Fira Sans", sans-serif', label: 'Fira Sans' },
  { value: '"Merriweather", serif', label: 'Merriweather' },
]

function generateId() {
  return `theme_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

export const useThemeStore = defineStore('themes', () => {
  const themes = ref([])
  const activeThemeId = ref(null)

  const activeTheme = computed(() =>
    themes.value.find((t) => t.id === activeThemeId.value) || null
  )

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const data = JSON.parse(saved)
        themes.value = data.themes || []
        activeThemeId.value = data.activeThemeId || null
      }
    } catch {
      // Corrupted data — start fresh
    }
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      themes: themes.value,
      activeThemeId: activeThemeId.value,
    }))
  }

  watch([themes, activeThemeId], persist, { deep: true })

  function applyTheme(props) {
    const root = document.documentElement
    if (!props) {
      // Clear all custom overrides
      Object.keys(DEFAULT_THEME_PROPS).forEach((key) => {
        root.style.removeProperty(key)
      })
      return
    }
    Object.entries(props).forEach(([key, value]) => {
      if (key === '--shadow-intensity') return
      root.style.setProperty(key, value)
    })
    // Shadow intensity scales all shadow opacities
    const intensity = parseFloat(props['--shadow-intensity'] ?? 1)
    root.style.setProperty('--shadow-sm', `0 1px 2px rgba(0,0,0,${(0.05 * intensity).toFixed(3)})`)
    root.style.setProperty('--shadow', `0 1px 3px rgba(0,0,0,${(0.1 * intensity).toFixed(3)}), 0 1px 2px rgba(0,0,0,${(0.06 * intensity).toFixed(3)})`)
    root.style.setProperty('--shadow-md', `0 4px 6px rgba(0,0,0,${(0.07 * intensity).toFixed(3)}), 0 2px 4px rgba(0,0,0,${(0.06 * intensity).toFixed(3)})`)
    root.style.setProperty('--shadow-lg', `0 10px 15px rgba(0,0,0,${(0.1 * intensity).toFixed(3)}), 0 4px 6px rgba(0,0,0,${(0.05 * intensity).toFixed(3)})`)
    // Derive tints from primary
    const primary = props['--color-primary'] || '#2068FF'
    const r = parseInt(primary.slice(1, 3), 16)
    const g = parseInt(primary.slice(3, 5), 16)
    const b = parseInt(primary.slice(5, 7), 16)
    root.style.setProperty('--color-primary-light', `rgba(${r},${g},${b},0.08)`)
    root.style.setProperty('--color-primary-tint', `rgba(${r},${g},${b},0.1)`)
    root.style.setProperty('--color-primary-border', `rgba(${r},${g},${b},0.3)`)
  }

  function activateTheme(id) {
    activeThemeId.value = id
    const theme = themes.value.find((t) => t.id === id)
    applyTheme(theme ? theme.props : null)
  }

  function deactivateTheme() {
    activeThemeId.value = null
    applyTheme(null)
  }

  function saveTheme(name, props) {
    const id = generateId()
    themes.value.push({ id, name, props: { ...props }, createdAt: new Date().toISOString() })
    return id
  }

  function updateTheme(id, name, props) {
    const idx = themes.value.findIndex((t) => t.id === id)
    if (idx === -1) return
    themes.value[idx] = { ...themes.value[idx], name, props: { ...props } }
    if (activeThemeId.value === id) applyTheme(props)
  }

  function deleteTheme(id) {
    themes.value = themes.value.filter((t) => t.id !== id)
    if (activeThemeId.value === id) deactivateTheme()
  }

  function exportTheme(id) {
    const theme = themes.value.find((t) => t.id === id)
    if (!theme) return null
    return JSON.stringify({ name: theme.name, props: theme.props }, null, 2)
  }

  function importTheme(json) {
    const data = JSON.parse(json)
    if (!data.name || !data.props) throw new Error('Invalid theme format')
    return saveTheme(data.name, data.props)
  }

  // Initialize
  load()
  if (activeThemeId.value) {
    const theme = themes.value.find((t) => t.id === activeThemeId.value)
    if (theme) applyTheme(theme.props)
  }

  return {
    themes,
    activeThemeId,
    activeTheme,
    activateTheme,
    deactivateTheme,
    saveTheme,
    updateTheme,
    deleteTheme,
    exportTheme,
    importTheme,
    applyTheme,
    DEFAULT_THEME_PROPS,
    FONT_OPTIONS,
  }
})
