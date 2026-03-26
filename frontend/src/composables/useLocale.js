import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLocaleStore } from '../stores/locale'

export function useLocale() {
  const store = useLocaleStore()
  const { t } = useI18n()
  const locale = computed(() => store.locale)

  function setLocale(code) {
    store.setLocale(code)
  }

  function formatNumber(value, options) {
    return new Intl.NumberFormat(locale.value, options).format(value)
  }

  function formatCompactNumber(value) {
    return new Intl.NumberFormat(locale.value, { notation: 'compact', maximumFractionDigits: 1 }).format(value)
  }

  function formatDecimal(value, fractionDigits = 1) {
    return new Intl.NumberFormat(locale.value, {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    }).format(value)
  }

  function formatPercent(value) {
    return new Intl.NumberFormat(locale.value, { style: 'percent' }).format(value)
  }

  function formatDate(date, options) {
    return new Intl.DateTimeFormat(locale.value, options).format(date instanceof Date ? date : new Date(date))
  }

  function formatShortDateTime(date) {
    return formatDate(date, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
  }

  function formatRelativeTime(timestamp) {
    const diff = Math.floor((Date.now() - timestamp) / 1000)
    const rtf = new Intl.RelativeTimeFormat(locale.value, { numeric: 'auto' })

    if (diff < 60) return rtf.format(-diff, 'second')
    if (diff < 3600) return rtf.format(-Math.floor(diff / 60), 'minute')
    if (diff < 86400) return rtf.format(-Math.floor(diff / 3600), 'hour')
    return rtf.format(-Math.floor(diff / 86400), 'day')
  }

  function formatSignedDecimal(value, fractionDigits = 1) {
    return new Intl.NumberFormat(locale.value, {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
      signDisplay: 'exceptZero',
    }).format(value)
  }

  return {
    locale,
    setLocale,
    supportedLocales: store.supportedLocales,
    t,
    formatNumber,
    formatCompactNumber,
    formatDecimal,
    formatPercent,
    formatDate,
    formatShortDateTime,
    formatRelativeTime,
    formatSignedDecimal,
  }
}
