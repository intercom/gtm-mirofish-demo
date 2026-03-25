import { createI18n } from 'vue-i18n'
import en from '../locales/en.json'

const STORAGE_KEY = 'mirofish-locale'

const savedLocale = localStorage.getItem(STORAGE_KEY)

const i18n = createI18n({
  legacy: false,
  locale: savedLocale || 'en',
  fallbackLocale: 'en',
  messages: { en },
})

export default i18n
