import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  BRAND_COLORS,
  brandColorScale,
  sentimentColorScale,
  quantitativeColorScale,
  formatCurrency,
  formatPercentage,
  formatNumber,
  axisFormatter,
  chartMargins,
  responsiveResize,
  createTooltip,
  chartTransitions,
  isDarkMode,
  themeColors,
} from '../chartUtils.js'

describe('BRAND_COLORS', () => {
  it('has the required Intercom brand colors', () => {
    expect(BRAND_COLORS.primary).toBe('#2068FF')
    expect(BRAND_COLORS.navy).toBe('#050505')
    expect(BRAND_COLORS.orange).toBe('#ff5600')
    expect(BRAND_COLORS.accent).toBe('#AA00FF')
  })

  it('has at least 10 colors total', () => {
    expect(Object.keys(BRAND_COLORS).length).toBeGreaterThanOrEqual(10)
  })
})

describe('brandColorScale', () => {
  it('returns d3 ordinal scale', () => {
    const scale = brandColorScale(['a', 'b', 'c'])
    expect(scale('a')).toBe('#2068FF')
    expect(scale('b')).toBe('#ff5600')
    expect(scale('c')).toBe('#AA00FF')
  })

  it('works without a domain', () => {
    const scale = brandColorScale()
    expect(typeof scale).toBe('function')
  })
})

describe('sentimentColorScale', () => {
  it('maps -1 to orange, 0 to primary, 1 to green', () => {
    const scale = sentimentColorScale()
    // d3.scaleLinear interpolates to rgb() strings
    expect(scale(-1)).toBe('rgb(255, 86, 0)')
    expect(scale(0)).toBe('rgb(32, 104, 255)')
    expect(scale(1)).toBe('rgb(0, 153, 0)')
  })

  it('clamps values outside [-1, 1]', () => {
    const scale = sentimentColorScale()
    expect(scale(-2)).toBe(scale(-1))
    expect(scale(2)).toBe(scale(1))
  })
})

describe('quantitativeColorScale', () => {
  it('returns a sequential scale', () => {
    const scale = quantitativeColorScale([0, 100])
    expect(typeof scale(0)).toBe('string')
    expect(typeof scale(50)).toBe('string')
    expect(typeof scale(100)).toBe('string')
  })

  it('defaults to [0, 1] domain', () => {
    const scale = quantitativeColorScale()
    expect(typeof scale(0.5)).toBe('string')
  })
})

describe('formatCurrency', () => {
  it('formats with default USD and 0 decimals', () => {
    expect(formatCurrency(1234)).toBe('$1,234')
  })

  it('supports custom decimals', () => {
    expect(formatCurrency(1234.56, { decimals: 2 })).toBe('$1,234.56')
  })

  it('supports custom currency', () => {
    const result = formatCurrency(1234, { currency: 'EUR' })
    expect(result).toContain('1,234')
  })
})

describe('formatPercentage', () => {
  it('formats with 1 decimal by default', () => {
    expect(formatPercentage(42.567)).toBe('42.6%')
  })

  it('supports custom decimals', () => {
    expect(formatPercentage(42.567, { decimals: 0 })).toBe('43%')
  })
})

describe('formatNumber', () => {
  it('abbreviates millions', () => {
    expect(formatNumber(2_500_000)).toBe('2.5M')
  })

  it('abbreviates thousands', () => {
    expect(formatNumber(1_500)).toBe('1.5K')
  })

  it('formats small numbers directly', () => {
    expect(formatNumber(42)).toBe('42')
  })

  it('supports custom decimals for small numbers', () => {
    expect(formatNumber(42.567, { decimals: 2 })).toBe('42.57')
  })
})

describe('axisFormatter', () => {
  it('returns number formatter by default', () => {
    const fn = axisFormatter()
    expect(fn(1500)).toBe('1.5K')
  })

  it('returns percentage formatter', () => {
    const fn = axisFormatter('percentage')
    expect(fn(42.5)).toBe('42.5%')
  })

  it('returns currency formatter', () => {
    const fn = axisFormatter('currency')
    expect(fn(1234)).toBe('$1,234')
  })

  it('returns round formatter', () => {
    const fn = axisFormatter('round')
    expect(fn(5)).toBe('R5')
  })

  it('falls back to number for unknown type', () => {
    const fn = axisFormatter('unknown')
    expect(fn(1500)).toBe('1.5K')
  })
})

describe('chartMargins', () => {
  it('has sm, md, lg presets', () => {
    for (const size of ['sm', 'md', 'lg']) {
      const m = chartMargins[size]
      expect(m).toHaveProperty('top')
      expect(m).toHaveProperty('right')
      expect(m).toHaveProperty('bottom')
      expect(m).toHaveProperty('left')
    }
  })

  it('sm margins are smaller than lg', () => {
    expect(chartMargins.sm.top).toBeLessThan(chartMargins.lg.top)
    expect(chartMargins.sm.left).toBeLessThan(chartMargins.lg.left)
  })
})

describe('responsiveResize', () => {
  it('returns an object with disconnect method', () => {
    const container = document.createElement('div')
    const handle = responsiveResize(container, vi.fn())
    expect(typeof handle.disconnect).toBe('function')
    handle.disconnect()
  })
})

describe('createTooltip', () => {
  it('returns tooltip controller with show/move/hide/remove', () => {
    const container = document.createElement('div')
    document.body.appendChild(container)

    const tip = createTooltip(container)
    expect(typeof tip.show).toBe('function')
    expect(typeof tip.move).toBe('function')
    expect(typeof tip.hide).toBe('function')
    expect(typeof tip.remove).toBe('function')

    tip.remove()
    container.remove()
  })

  it('appends a div to the container', () => {
    const container = document.createElement('div')
    document.body.appendChild(container)

    createTooltip(container)
    const tooltipEl = container.querySelector('div')
    expect(tooltipEl).not.toBeNull()

    container.remove()
  })
})

describe('chartTransitions', () => {
  it('has duration, stagger, and ease', () => {
    expect(chartTransitions.duration).toBe(600)
    expect(chartTransitions.stagger).toBe(80)
    expect(typeof chartTransitions.ease).toBe('function')
  })
})

describe('isDarkMode', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark')
  })

  it('returns false when dark class absent', () => {
    expect(isDarkMode()).toBe(false)
  })

  it('returns true when dark class present', () => {
    document.documentElement.classList.add('dark')
    expect(isDarkMode()).toBe(true)
  })
})

describe('themeColors', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark')
  })

  it('returns light theme colors by default', () => {
    const colors = themeColors()
    expect(colors.text).toBe('#050505')
    expect(colors.surface).toBe('#ffffff')
  })

  it('returns dark theme colors when dark mode is active', () => {
    document.documentElement.classList.add('dark')
    const colors = themeColors()
    expect(colors.text).toBe('#e0e0e0')
    expect(colors.surface).toBe('#1a1a2e')
  })
})
