import { watch } from 'vue'
import { useI18n } from 'vue-i18n'

const STORAGE_KEY = 'mirofish-language'

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', flag: '🇺🇸' },
  { code: 'es', label: 'Espanol', flag: '🇪🇸' },
  { code: 'fr', label: 'Francais', flag: '🇫🇷' },
  { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { code: 'ja', label: '日本語', flag: '🇯🇵' },
  { code: 'pt', label: 'Portugues', flag: '🇧🇷' },
]

export function useLanguage() {
  const { locale } = useI18n()

  function setLanguage(code) {
    const valid = SUPPORTED_LANGUAGES.find((l) => l.code === code)
    if (!valid) return
    locale.value = code
    localStorage.setItem(STORAGE_KEY, code)
    document.documentElement.lang = code
  }

  watch(
    locale,
    (lang) => {
      document.documentElement.lang = lang
    },
    { immediate: true },
  )

  return {
    locale,
    languages: SUPPORTED_LANGUAGES,
    setLanguage,
  }
}
