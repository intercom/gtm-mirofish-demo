import * as d3 from 'd3'
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme'

// ── Brand Palette ────────────────────────────────────────────────────────────

export const BRAND_COLORS = {
  primary: '#2068FF',
  navy: '#050505',
  orange: '#ff5600',
  accent: '#AA00FF',
  green: '#009900',
  teal: '#0891B2',
  rose: '#E11D48',
  amber: '#D97706',
  indigo: '#4F46E5',
  emerald: '#059669',
}

const CATEGORICAL_PALETTE = [
  BRAND_COLORS.primary,
  BRAND_COLORS.orange,
  BRAND_COLORS.accent,
  BRAND_COLORS.green,
  BRAND_COLORS.teal,
  BRAND_COLORS.rose,
  BRAND_COLORS.amber,
  BRAND_COLORS.indigo,
  BRAND_COLORS.emerald,
  BRAND_COLORS.navy,
]

// ── Theme-Aware Chart Palettes ──────────────────────────────────────────────

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

// ── Dark Mode Detection ──────────────────────────────────────────────────────

export function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

/**
 * Returns theme-aware chart colors by reading the current DOM theme state.
 * Call inside D3 render functions — reads `.dark` class on <html>.
 */
export function getChartColors() {
  return isDarkMode() ? darkPalette : lightPalette
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

// ── Color Scales ─────────────────────────────────────────────────────────────

export function brandColorScale(domain) {
  return d3.scaleOrdinal()
    .domain(domain || [])
    .range(CATEGORICAL_PALETTE)
}

export function sentimentColorScale() {
  return d3.scaleLinear()
    .domain([-1, 0, 1])
    .range([BRAND_COLORS.orange, BRAND_COLORS.primary, BRAND_COLORS.green])
    .clamp(true)
}

export function quantitativeColorScale(domain = [0, 1]) {
  return d3.scaleSequential()
    .domain(domain)
    .interpolator(d3.interpolateBlues)
}

// ── Number Formatters ────────────────────────────────────────────────────────

export function formatCurrency(value, { decimals = 0, currency = 'USD' } = {}) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercentage(value, { decimals = 1 } = {}) {
  return `${Number(value).toFixed(decimals)}%`
}

export function formatNumber(value, { decimals = 0 } = {}) {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return Number(value).toFixed(decimals)
}

// ── Axis Formatter ───────────────────────────────────────────────────────────

export function axisFormatter(type = 'number') {
  const formatters = {
    number: formatNumber,
    percentage: formatPercentage,
    currency: formatCurrency,
    round: (v) => `R${v}`,
  }
  return formatters[type] || formatters.number
}

// ── Standard Margins ─────────────────────────────────────────────────────────

export const chartMargins = {
  sm: { top: 12, right: 16, bottom: 28, left: 36 },
  md: { top: 24, right: 24, bottom: 40, left: 48 },
  lg: { top: 56, right: 60, bottom: 80, left: 100 },
}

// ── Responsive Resize ────────────────────────────────────────────────────────

export function responsiveResize(container, renderFn, { debounce = 200 } = {}) {
  let timer = null
  const observer = new ResizeObserver(() => {
    clearTimeout(timer)
    timer = setTimeout(renderFn, debounce)
  })
  observer.observe(container)

  return {
    disconnect() {
      observer.disconnect()
      clearTimeout(timer)
    },
  }
}

// ── Tooltip ──────────────────────────────────────────────────────────────────

export function createTooltip(container) {
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('max-width', '240px')
    .style('line-height', '1.4')

  return {
    show(html, event) {
      tooltip.html(html).style('opacity', 1)
      if (event) this.move(event)
    },
    move(event) {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    },
    hide() {
      tooltip.style('opacity', 0)
    },
    remove() {
      tooltip.remove()
    },
  }
}

// ── Chart Animation Defaults ─────────────────────────────────────────────────

export const chartTransitions = {
  duration: 600,
  stagger: 80,
  ease: d3.easeCubicOut,
}
