import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const css = readFileSync(
  resolve(__dirname, '../assets/brand-tokens.css'),
  'utf-8'
)

/**
 * Extract all CSS custom properties from a given selector block.
 * Returns an array of property names (e.g., ['--color-primary', '--btn-radius']).
 */
function extractProperties(source, selector) {
  const pattern =
    selector === ':root'
      ? /^:root\s*\{([^}]+)\}/m
      : new RegExp(`\\.${selector}\\s*\\{([^}]+)\\}`, 'm')
  const match = source.match(pattern)
  if (!match) return []
  return [...match[1].matchAll(/--([\w-]+)\s*:/g)].map((m) => `--${m[1]}`)
}

const rootProps = extractProperties(css, ':root')
const darkProps = extractProperties(css, 'dark')

describe('brand-tokens.css', () => {
  it('defines :root custom properties', () => {
    expect(rootProps.length).toBeGreaterThan(0)
  })

  describe('brand colors', () => {
    const required = [
      '--color-primary',
      '--color-primary-hover',
      '--color-primary-active',
      '--color-primary-light',
      '--color-primary-border',
      '--color-navy',
      '--color-navy-light',
      '--color-fin-orange',
      '--color-accent',
      '--color-success',
      '--color-warning',
      '--color-error',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('neutrals', () => {
    const required = [
      '--color-bg',
      '--color-surface',
      '--color-border',
      '--color-text',
      '--color-text-secondary',
      '--color-text-muted',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('typography scale', () => {
    const required = [
      '--font-family',
      '--text-xs',
      '--text-sm',
      '--text-base',
      '--text-lg',
      '--text-xl',
      '--text-2xl',
      '--text-3xl',
      '--text-4xl',
      '--leading-tight',
      '--leading-normal',
      '--font-medium',
      '--font-semibold',
      '--font-bold',
      '--letter-spacing-tight',
      '--letter-spacing-tighter',
      '--letter-spacing-tightest',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('spacing system', () => {
    const required = [
      '--space-1',
      '--space-2',
      '--space-4',
      '--space-8',
      '--space-16',
      '--radius-sm',
      '--radius',
      '--radius-lg',
      '--radius-full',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('component tokens: buttons', () => {
    const required = [
      '--btn-primary-bg',
      '--btn-primary-bg-hover',
      '--btn-primary-text',
      '--btn-secondary-bg',
      '--btn-secondary-border',
      '--btn-dark-bg',
      '--btn-ghost-bg',
      '--btn-disabled-opacity',
      '--btn-radius',
      '--btn-padding-x',
      '--btn-padding-y',
      '--btn-font-weight',
      '--btn-font-size',
      '--btn-transition',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('component tokens: cards', () => {
    const required = [
      '--card-bg',
      '--card-bg-hover',
      '--card-border',
      '--card-radius',
      '--card-padding',
      '--card-shadow',
      '--card-shadow-hover',
      '--card-transition',
      '--card-highlight-bg',
      '--card-highlight-border',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('component tokens: inputs', () => {
    const required = [
      '--input-bg',
      '--input-border',
      '--input-border-focus',
      '--input-ring',
      '--input-text',
      '--input-placeholder',
      '--input-radius',
      '--input-padding-x',
      '--input-padding-y',
      '--input-font-size',
      '--input-transition',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('component tokens: badges', () => {
    const required = [
      '--badge-primary-bg',
      '--badge-primary-text',
      '--badge-secondary-bg',
      '--badge-secondary-text',
      '--badge-orange-bg',
      '--badge-success-bg',
      '--badge-error-bg',
      '--badge-radius',
      '--badge-padding-x',
      '--badge-font-size',
      '--badge-font-weight',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('dark mode', () => {
    it('has .dark overrides', () => {
      expect(darkProps.length).toBeGreaterThan(0)
    })

    const required = [
      '--color-bg',
      '--color-surface',
      '--color-border',
      '--color-text',
      '--color-text-secondary',
      '--color-text-muted',
    ]
    for (const prop of required) {
      it(`overrides ${prop} in dark mode`, () => {
        expect(darkProps).toContain(prop)
      })
    }
  })

  describe('valid CSS values', () => {
    it('does not contain undefined or null values', () => {
      expect(css).not.toMatch(/:\s*(undefined|null)\s*;/)
    })

    it('every property has a value', () => {
      expect(css).not.toMatch(/--[\w-]+\s*:\s*;/)
    })
  })
})
