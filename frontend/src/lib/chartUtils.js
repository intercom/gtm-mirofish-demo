import * as d3 from 'd3'

// ── Brand Palette ────────────────────────────────────────────────────────────
// Primary Intercom colors + 6 additional chart-safe colors for categorical data.

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

// ── Dark Mode Detection ──────────────────────────────────────────────────────

export function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

export function themeColors() {
  const dark = isDarkMode()
  return {
    text: dark ? '#e0e0e0' : '#050505',
    textSecondary: dark ? '#aaaaaa' : '#555555',
    textMuted: dark ? '#666666' : '#888888',
    gridLine: dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
    gridLineStrong: dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)',
    surface: dark ? '#1a1a2e' : '#ffffff',
    barBg: dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
  }
}
