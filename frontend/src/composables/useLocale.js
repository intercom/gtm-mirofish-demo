import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const STORAGE_KEY = 'mirofish-locale'

const SUPPORTED_LOCALES = [
  { code: 'en', label: 'English' },
]

export function useLocale() {
  const { locale, t } = useI18n()

  const currentLocale = computed(() => locale.value)

  function setLocale(code) {
    if (!SUPPORTED_LOCALES.some((l) => l.code === code)) return
    locale.value = code
    localStorage.setItem(STORAGE_KEY, code)
    document.documentElement.lang = code
  }

  return { currentLocale, setLocale, supportedLocales: SUPPORTED_LOCALES, t }
}
