import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

const STORAGE_KEY = 'mirofish-theme'
const DARK_ROUTES = new Set(['landing', 'login'])

// Module-level shared state so all components see the same value
const preference = ref(localStorage.getItem(STORAGE_KEY) || 'auto')

function systemPrefersDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function resolveTheme(pref, routeName) {
  if (pref === 'light') return 'light'
  if (pref === 'dark') return 'dark'
  if (pref === 'system') return systemPrefersDark() ? 'dark' : 'light'
  // 'auto': dark for landing/login, light for app views
  return DARK_ROUTES.has(routeName) ? 'dark' : 'light'
}

function applyClass(isDark) {
  document.documentElement.classList.toggle('dark', isDark)
}

export function useTheme() {
  const route = useRoute()

  const isDark = computed(() => resolveTheme(preference.value, route?.name) === 'dark')

  function apply() {
    applyClass(isDark.value)
  }

  function setTheme(value) {
    preference.value = value
    localStorage.setItem(STORAGE_KEY, value)
    apply()
  }

  watch(() => route?.name, apply)
  watch(preference, apply)

  let mq
  onMounted(() => {
    mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', apply)
    apply()
  })

  onUnmounted(() => {
    mq?.removeEventListener('change', apply)
  })

  return { preference, isDark, setTheme }
}

// Used by the FOUC-prevention script (not Vue-dependent)
export { resolveTheme, applyClass, STORAGE_KEY, DARK_ROUTES }
