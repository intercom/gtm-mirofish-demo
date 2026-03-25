import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish-locale'

const SUPPORTED_LOCALES = [
  { code: 'en-US', label: 'English (US)' },
  { code: 'en-GB', label: 'English (UK)' },
  { code: 'de-DE', label: 'Deutsch' },
  { code: 'fr-FR', label: 'Français' },
  { code: 'ja-JP', label: '日本語' },
  { code: 'zh-CN', label: '中文 (简体)' },
  { code: 'pt-BR', label: 'Português (BR)' },
  { code: 'es-ES', label: 'Español' },
]

function detectBrowserLocale() {
  const nav = navigator.language || navigator.languages?.[0]
  if (!nav) return 'en-US'
  const match = SUPPORTED_LOCALES.find(l => l.code === nav)
  if (match) return match.code
  const prefix = nav.split('-')[0]
  const prefixMatch = SUPPORTED_LOCALES.find(l => l.code.startsWith(prefix))
  return prefixMatch?.code || 'en-US'
}

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref('en-US')

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      locale.value = saved && SUPPORTED_LOCALES.some(l => l.code === saved)
        ? saved
        : detectBrowserLocale()
    } catch {
      locale.value = detectBrowserLocale()
    }
  }

  function setLocale(code) {
    if (SUPPORTED_LOCALES.some(l => l.code === code)) {
      locale.value = code
    }
  }

  watch(locale, (val) => {
    try { localStorage.setItem(STORAGE_KEY, val) } catch {}
  })

  load()

  return { locale, setLocale, supportedLocales: SUPPORTED_LOCALES }
})
