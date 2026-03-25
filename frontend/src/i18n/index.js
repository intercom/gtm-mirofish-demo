import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import ja from './locales/ja.json'

const savedLocale = typeof localStorage !== 'undefined'
  ? localStorage.getItem('mirofish-locale')
  : null

const i18n = createI18n({
  legacy: false,
  locale: savedLocale || 'en',
  fallbackLocale: 'en',
  messages: { en, ja },
})

export default i18n
