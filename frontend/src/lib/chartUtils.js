import { computed } from 'vue'
import { useTheme } from '../composables/useTheme'

const lightPalette = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',

  text: '#050505',
  textSecondary: '#555555',
  textMuted: '#888888',
  surface: '#ffffff',
  border: 'rgba(0,0,0,0.1)',

  gridLine: 'rgba(0,0,0,0.06)',
  gridLineStrong: 'rgba(0,0,0,0.15)',
  barBg: 'rgba(0,0,0,0.03)',
  connectorLine: 'rgba(0,0,0,0.15)',

  areaPositive: 'rgba(0,153,0,0.08)',
  areaNegative: 'rgba(255,86,0,0.08)',
  stackPositive: 'rgba(0,153,0,0.5)',
  stackNeutral: 'rgba(32,104,255,0.3)',
  stackNegative: 'rgba(255,86,0,0.5)',
  stackGrid: 'rgba(255,255,255,0.4)',
}

const darkPalette = {
  primary: '#5A93FF',
  orange: '#FF8040',
  purple: '#CC66FF',
  green: '#66BB6A',

  text: '#e0e0e0',
  textSecondary: '#aaaaaa',
  textMuted: '#666666',
  surface: '#1a1a2e',
  border: 'rgba(255,255,255,0.1)',

  gridLine: 'rgba(255,255,255,0.06)',
  gridLineStrong: 'rgba(255,255,255,0.15)',
  barBg: 'rgba(255,255,255,0.04)',
  connectorLine: 'rgba(255,255,255,0.15)',

  areaPositive: 'rgba(102,187,106,0.15)',
  areaNegative: 'rgba(255,128,64,0.15)',
  stackPositive: 'rgba(102,187,106,0.5)',
  stackNeutral: 'rgba(90,147,255,0.3)',
  stackNegative: 'rgba(255,128,64,0.5)',
  stackGrid: 'rgba(255,255,255,0.1)',
}

/**
 * Returns theme-aware chart colors by reading the current DOM theme state.
 * Call inside D3 render functions — reads `.dark` class on <html>.
 */
export function getChartColors() {
  const isDark = document.documentElement.classList.contains('dark')
  return isDark ? darkPalette : lightPalette
}

/**
 * Reactive composable for Vue components.
 * Returns a computed colors ref that updates when the theme toggles,
 * plus isDark for triggering chart re-renders via watch().
 */
export function useChartColors() {
  const { isDark } = useTheme()
  const colors = computed(() => isDark.value ? darkPalette : lightPalette)
  return { colors, isDark }
}
