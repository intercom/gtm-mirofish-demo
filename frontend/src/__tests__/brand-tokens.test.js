import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const css = readFileSync(
  resolve(__dirname, '../assets/brand-tokens.css'),
  'utf-8'
)

/**
 * Extract all CSS custom properties from a given selector block.
 * Returns an array of property names (e.g., ['--color-primary', '--btn-primary-bg']).
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

  describe('typography', () => {
    const required = [
      '--font-family',
    ]
    for (const prop of required) {
      it(`includes ${prop}`, () => {
        expect(rootProps).toContain(prop)
      })
    }
  })

  describe('radius', () => {
    const required = [
      '--radius-sm',
      '--radius-lg',
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
      '--btn-ghost-bg-hover',
      '--btn-ghost-text',
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
      '--card-border',
      '--card-radius',
      '--card-shadow',
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
      '--input-ring',
      '--input-text',
      '--input-placeholder',
      '--input-radius',
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
      '--badge-orange-bg-soft',
      '--badge-success-bg-soft',
      '--badge-error-bg-soft',
      '--badge-padding-x',
      '--badge-font-size',
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
