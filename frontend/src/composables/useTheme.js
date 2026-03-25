import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'mirofish-theme'
const VALID_THEMES = ['system', 'light', 'dark']

const preference = ref('system')
const systemIsDark = ref(false)
const hasExplicitPreference = ref(false)
const routeDefault = ref(null)

let mediaQuery = null
let initialized = false

function onSystemChange(e) {
  systemIsDark.value = e.matches
}

function applyClass(dark) {
  document.documentElement.classList.toggle('dark', dark)
}

const isDark = computed(() => {
  if (preference.value === 'dark') return true
  if (preference.value === 'light') return false
  if (!hasExplicitPreference.value && routeDefault.value) {
    return routeDefault.value === 'dark'
  }
  return systemIsDark.value
})

const systemPreference = computed(() => systemIsDark.value ? 'dark' : 'light')

watch(isDark, (dark) => applyClass(dark), { flush: 'sync' })

export function useTheme() {
  if (!initialized) {
    initialized = true

    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && VALID_THEMES.includes(stored)) {
      preference.value = stored
      hasExplicitPreference.value = true
    }

    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemIsDark.value = mediaQuery.matches
    mediaQuery.addEventListener('change', onSystemChange)

    applyClass(isDark.value)
  }

  function setTheme(value) {
    if (!VALID_THEMES.includes(value)) return
    preference.value = value
    hasExplicitPreference.value = true
    localStorage.setItem(STORAGE_KEY, value)
  }

  function setRouteDefault(value) {
    routeDefault.value = value
  }

  return { preference, isDark, systemPreference, setTheme, setRouteDefault }
}
