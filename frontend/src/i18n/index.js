import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import ja from './locales/ja.json'

const STORAGE_KEY = 'mirofish-locale'

const savedLocale = typeof localStorage !== 'undefined'
  ? localStorage.getItem(STORAGE_KEY)
  : null

const i18n = createI18n({
  legacy: false,
  locale: savedLocale || 'en',
  fallbackLocale: 'en',
  messages: { en, ja },
})

export default i18n
