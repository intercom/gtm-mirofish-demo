import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const css = readFileSync(resolve(__dirname, 'brand-tokens.css'), 'utf-8')

function extractCustomProperties(text) {
  const props = new Map()
  for (const match of text.matchAll(/--([a-z][a-z0-9-]*):\s*([^;]+);/g)) {
    props.set(`--${match[1]}`, match[2].trim())
  }
  return props
}

const rootBlock = css.match(/:root\s*\{([^}]+)\}/s)?.[1] ?? ''
const darkBlock = css.match(/\.dark\s*\{([^}]+)\}/s)?.[1] ?? ''
const rootProps = extractCustomProperties(rootBlock)
const darkProps = extractCustomProperties(darkBlock)

describe('brand-tokens.css', () => {
  describe('brand colors', () => {
    it('defines Intercom primary blue', () => {
      expect(rootProps.get('--color-primary')).toBe('#2068FF')
    })

    it('defines navy', () => {
      expect(rootProps.get('--color-navy')).toBe('#050505')
    })

    it('defines Fin orange', () => {
      expect(rootProps.get('--color-fin-orange')).toBe('#ff5600')
    })

    it('defines accent purple', () => {
      expect(rootProps.get('--color-accent')).toBe('#AA00FF')
    })

    it('defines semantic status colors', () => {
      expect(rootProps.has('--color-success')).toBe(true)
      expect(rootProps.has('--color-warning')).toBe(true)
      expect(rootProps.has('--color-error')).toBe(true)
    })
  })

  describe('typography scale', () => {
    const sizes = ['--text-xs', '--text-sm', '--text-base', '--text-lg',
      '--text-xl', '--text-2xl', '--text-3xl', '--text-4xl']

    it('defines all font size steps', () => {
      for (const size of sizes) {
        expect(rootProps.has(size), `missing ${size}`).toBe(true)
      }
    })

    it('font sizes increase monotonically', () => {
      const values = sizes.map(s => parseFloat(rootProps.get(s)))
      for (let i = 1; i < values.length; i++) {
        expect(values[i]).toBeGreaterThan(values[i - 1])
      }
    })

    it('defines line heights', () => {
      expect(rootProps.has('--leading-tight')).toBe(true)
      expect(rootProps.has('--leading-normal')).toBe(true)
      expect(rootProps.has('--leading-relaxed')).toBe(true)
    })

    it('defines font weights', () => {
      expect(rootProps.has('--font-medium')).toBe(true)
      expect(rootProps.has('--font-semibold')).toBe(true)
      expect(rootProps.has('--font-bold')).toBe(true)
    })

    it('defines font families', () => {
      expect(rootProps.has('--font-family')).toBe(true)
      expect(rootProps.has('--font-mono')).toBe(true)
    })
  })

  describe('spacing system', () => {
    const steps = ['--space-1', '--space-2', '--space-3', '--space-4',
      '--space-6', '--space-8', '--space-10', '--space-12', '--space-16']

    it('defines all spacing steps', () => {
      for (const step of steps) {
        expect(rootProps.has(step), `missing ${step}`).toBe(true)
      }
    })

    it('spacing values increase monotonically', () => {
      const values = steps.map(s => parseFloat(rootProps.get(s)))
      for (let i = 1; i < values.length; i++) {
        expect(values[i]).toBeGreaterThan(values[i - 1])
      }
    })
  })

  describe('component tokens: buttons', () => {
    it('defines button structure tokens', () => {
      expect(rootProps.has('--btn-padding-x')).toBe(true)
      expect(rootProps.has('--btn-padding-y')).toBe(true)
      expect(rootProps.has('--btn-radius')).toBe(true)
      expect(rootProps.has('--btn-font-size')).toBe(true)
      expect(rootProps.has('--btn-font-weight')).toBe(true)
    })

    it('defines primary button variant', () => {
      expect(rootProps.has('--btn-primary-bg')).toBe(true)
      expect(rootProps.has('--btn-primary-bg-hover')).toBe(true)
      expect(rootProps.has('--btn-primary-text')).toBe(true)
    })

    it('defines secondary button variant', () => {
      expect(rootProps.has('--btn-secondary-bg')).toBe(true)
      expect(rootProps.has('--btn-secondary-bg-hover')).toBe(true)
      expect(rootProps.has('--btn-secondary-text')).toBe(true)
      expect(rootProps.has('--btn-secondary-border')).toBe(true)
    })

    it('defines dark button variant', () => {
      expect(rootProps.has('--btn-dark-bg')).toBe(true)
      expect(rootProps.has('--btn-dark-bg-hover')).toBe(true)
      expect(rootProps.has('--btn-dark-text')).toBe(true)
    })
  })

  describe('component tokens: cards', () => {
    it('defines card structure tokens', () => {
      expect(rootProps.has('--card-bg')).toBe(true)
      expect(rootProps.has('--card-border')).toBe(true)
      expect(rootProps.has('--card-radius')).toBe(true)
      expect(rootProps.has('--card-padding')).toBe(true)
      expect(rootProps.has('--card-padding-sm')).toBe(true)
    })

    it('defines highlight card variant', () => {
      expect(rootProps.has('--card-highlight-bg')).toBe(true)
      expect(rootProps.has('--card-highlight-border')).toBe(true)
      expect(rootProps.has('--card-highlight-bg-hover')).toBe(true)
    })

    it('defines info card variant', () => {
      expect(rootProps.has('--card-info-bg')).toBe(true)
      expect(rootProps.has('--card-info-border')).toBe(true)
    })
  })

  describe('component tokens: inputs', () => {
    it('defines input structure tokens', () => {
      expect(rootProps.has('--input-bg')).toBe(true)
      expect(rootProps.has('--input-border')).toBe(true)
      expect(rootProps.has('--input-radius')).toBe(true)
      expect(rootProps.has('--input-padding-x')).toBe(true)
      expect(rootProps.has('--input-padding-y')).toBe(true)
      expect(rootProps.has('--input-font-size')).toBe(true)
      expect(rootProps.has('--input-ring')).toBe(true)
      expect(rootProps.has('--input-placeholder')).toBe(true)
    })
  })

  describe('component tokens: badges', () => {
    it('defines badge structure tokens', () => {
      expect(rootProps.has('--badge-padding-x')).toBe(true)
      expect(rootProps.has('--badge-padding-y')).toBe(true)
      expect(rootProps.has('--badge-radius')).toBe(true)
      expect(rootProps.has('--badge-font-size')).toBe(true)
      expect(rootProps.has('--badge-font-weight')).toBe(true)
    })

    it('defines primary badge variant', () => {
      expect(rootProps.has('--badge-primary-bg')).toBe(true)
      expect(rootProps.has('--badge-primary-text')).toBe(true)
    })

    it('defines status badge variants', () => {
      for (const status of ['success', 'warning', 'error', 'info']) {
        expect(rootProps.has(`--badge-${status}-bg`), `missing --badge-${status}-bg`).toBe(true)
        expect(rootProps.has(`--badge-${status}-text`), `missing --badge-${status}-text`).toBe(true)
      }
    })
  })

  describe('dark mode', () => {
    it('overrides neutral colors', () => {
      expect(darkProps.has('--color-bg')).toBe(true)
      expect(darkProps.has('--color-surface')).toBe(true)
      expect(darkProps.has('--color-text')).toBe(true)
    })

    it('overrides badge status colors for legibility', () => {
      expect(darkProps.has('--badge-success-text-soft')).toBe(true)
      expect(darkProps.has('--badge-warning-text-soft')).toBe(true)
      expect(darkProps.has('--badge-error-text-soft')).toBe(true)
    })
  })
})
