import { createI18n } from 'vue-i18n'
import en from '../locales/en.json'
import es from '../locales/es.json'
import fr from '../locales/fr.json'
import de from '../locales/de.json'
import ja from '../locales/ja.json'
import pt from '../locales/pt.json'

const LOCALE_STORAGE_KEY = 'mirofish-locale'

function getInitialLanguage() {
  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (saved) return saved.split('-')[0]
  } catch {}
  const browserLang = navigator.language?.split('-')[0]
  if (['en', 'es', 'fr', 'de', 'ja', 'pt'].includes(browserLang)) {
    return browserLang
  }
  return 'en'
}

const i18n = createI18n({
  legacy: false,
  locale: getInitialLanguage(),
  fallbackLocale: 'en',
  messages: { en, es, fr, de, ja, pt },
})

export default i18n
