import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'mirofish-dir'

const RTL_LANGUAGES = new Set([
  'ar', 'he', 'fa', 'ur', 'ps', 'sd', 'ckb', 'ug', 'dv',
])

const override = ref(null)
let initialized = false

function isRTLLocale(locale) {
  const lang = locale?.split('-')[0]?.toLowerCase()
  return RTL_LANGUAGES.has(lang)
}

function applyDir(dir) {
  document.documentElement.dir = dir
  document.documentElement.lang = document.documentElement.lang || 'en'
}

const isRTL = computed(() => {
  if (override.value === 'rtl') return true
  if (override.value === 'ltr') return false
  return false
})

const dir = computed(() => isRTL.value ? 'rtl' : 'ltr')

watch(dir, (val) => applyDir(val), { flush: 'sync' })

export function useRTL() {
  if (!initialized) {
    initialized = true

    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'rtl' || stored === 'ltr') {
      override.value = stored
    }

    applyDir(dir.value)
  }

  function setDirection(value) {
    if (value !== 'rtl' && value !== 'ltr' && value !== 'auto') return
    override.value = value === 'auto' ? null : value
    if (value === 'auto') {
      localStorage.removeItem(STORAGE_KEY)
    } else {
      localStorage.setItem(STORAGE_KEY, value)
    }
  }

  function setDirectionFromLocale(locale) {
    override.value = null
    localStorage.removeItem(STORAGE_KEY)
    if (isRTLLocale(locale)) {
      override.value = 'rtl'
    }
  }

  return { isRTL, dir, override, setDirection, setDirectionFromLocale, isRTLLocale }
}
