import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'mirofish-theme'
const VALID_THEMES = ['system', 'light', 'dark']

const preference = ref('system')
const systemIsDark = ref(false)

let mediaQuery = null
let initialized = false

function onSystemChange(e) {
  systemIsDark.value = e.matches
}

function applyClass(dark) {
  document.documentElement.classList.toggle('dark', dark)
}

export function useTheme() {
  if (!initialized) {
    initialized = true

    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && VALID_THEMES.includes(stored)) {
      preference.value = stored
    }

    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemIsDark.value = mediaQuery.matches
    mediaQuery.addEventListener('change', onSystemChange)
  }

  const isDark = computed(() => {
    if (preference.value === 'dark') return true
    if (preference.value === 'light') return false
    return systemIsDark.value
  })

  watch(isDark, (dark) => applyClass(dark), { immediate: true, flush: 'sync' })

  function setTheme(value) {
    if (!VALID_THEMES.includes(value)) return
    preference.value = value
    localStorage.setItem(STORAGE_KEY, value)
  }

  return { preference, isDark, setTheme }
}
