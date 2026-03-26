import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import es from './locales/es.json'
import fr from './locales/fr.json'
import de from './locales/de.json'
import ja from './locales/ja.json'
import pt from './locales/pt.json'

const STORAGE_KEY = 'mirofish-language'

function getInitialLocale() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored && ['en', 'es', 'fr', 'de', 'ja', 'pt'].includes(stored)) {
    return stored
  }
  const browserLang = navigator.language?.split('-')[0]
  if (['en', 'es', 'fr', 'de', 'ja', 'pt'].includes(browserLang)) {
    return browserLang
  }
  return 'en'
}

const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: 'en',
  messages: { en, es, fr, de, ja, pt },
})

export default i18n
