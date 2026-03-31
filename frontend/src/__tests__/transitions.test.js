import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const styleCss = readFileSync(resolve(__dirname, '../style.css'), 'utf-8')
const appVue = readFileSync(resolve(__dirname, '../App.vue'), 'utf-8')

describe('Transition CSS classes', () => {
  it('defines direction-aware page transition classes', () => {
    expect(styleCss).toContain('.page-fade-enter-active')
    expect(styleCss).toContain('.page-fade-leave-active')
    expect(styleCss).toContain('.page-slide-left-enter-active')
    expect(styleCss).toContain('.page-slide-left-leave-active')
    expect(styleCss).toContain('.page-slide-right-enter-active')
    expect(styleCss).toContain('.page-slide-right-leave-active')
  })

  it('page-slide-left uses translateX for forward navigation', () => {
    expect(styleCss).toContain('.page-slide-left-enter-from')
    expect(styleCss).toContain('.page-slide-left-leave-to')
    expect(styleCss).toMatch(/\.page-slide-left-enter-from[\s\S]*?translateX/)
    expect(styleCss).toMatch(/\.page-slide-left-leave-to[\s\S]*?translateX/)
  })

  it('page-slide-right uses translateX for backward navigation', () => {
    expect(styleCss).toContain('.page-slide-right-enter-from')
    expect(styleCss).toContain('.page-slide-right-leave-to')
    expect(styleCss).toMatch(/\.page-slide-right-enter-from[\s\S]*?translateX/)
    expect(styleCss).toMatch(/\.page-slide-right-leave-to[\s\S]*?translateX/)
  })

  it('page-fade uses opacity for same-level navigation', () => {
    expect(styleCss).toContain('.page-fade-enter-from')
    expect(styleCss).toContain('.page-fade-leave-to')
  })

  it('respects prefers-reduced-motion', () => {
    expect(styleCss).toContain('prefers-reduced-motion: reduce')
  })

  it('defines fade transition classes', () => {
    expect(styleCss).toContain('.fade-enter-active')
    expect(styleCss).toContain('.fade-leave-active')
    expect(styleCss).toContain('.fade-enter-from')
    expect(styleCss).toContain('.fade-leave-to')
  })

  it('defines slide-up transition for chat messages', () => {
    expect(styleCss).toContain('.slide-up-enter-active')
    expect(styleCss).toContain('.slide-up-enter-from')
  })

  it('uses brand token transition durations', () => {
    expect(styleCss).toContain('var(--transition-base)')
  })

  it('defines modal-overlay transition classes', () => {
    expect(styleCss).toContain('.modal-overlay-enter-active')
    expect(styleCss).toContain('.modal-overlay-leave-active')
    expect(styleCss).toContain('.modal-overlay-enter-from')
    expect(styleCss).toContain('.modal-overlay-leave-to')
  })

  it('defines modal-content transition with scale transform', () => {
    expect(styleCss).toContain('.modal-content-enter-active')
    expect(styleCss).toContain('.modal-content-leave-active')
    expect(styleCss).toMatch(/\.modal-content-enter-from[\s\S]*?scale/)
    expect(styleCss).toMatch(/\.modal-content-leave-to[\s\S]*?scale/)
  })

  it('defines panel-right transition classes', () => {
    expect(styleCss).toContain('.panel-right-enter-active')
    expect(styleCss).toContain('.panel-right-leave-active')
    expect(styleCss).toMatch(/\.panel-right-enter-from[\s\S]*?translateX/)
    expect(styleCss).toMatch(/\.panel-right-leave-to[\s\S]*?translateX/)
  })
})

describe('App.vue page transition', () => {
  it('wraps router-view in dynamic Transition with usePageTransition', () => {
    expect(appVue).toContain(':name="transitionName"')
    expect(appVue).toContain('mode="out-in"')
    expect(appVue).toContain('<router-view')
    expect(appVue).toContain('usePageTransition')
  })

  it('imports usePageTransition composable', () => {
    expect(appVue).toContain("import { usePageTransition } from './composables/usePageTransition'")
  })
})
