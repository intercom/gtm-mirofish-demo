import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const styleCss = readFileSync(resolve(__dirname, '../style.css'), 'utf-8')
const appVue = readFileSync(resolve(__dirname, '../App.vue'), 'utf-8')

describe('Transition CSS classes', () => {
  it('defines directional page transition classes', () => {
    expect(styleCss).toContain('.page-forward-enter-active')
    expect(styleCss).toContain('.page-forward-leave-active')
    expect(styleCss).toContain('.page-back-enter-active')
    expect(styleCss).toContain('.page-back-leave-active')
  })

  it('page transitions use fade + directional slide', () => {
    expect(styleCss).toContain('.page-forward-enter-from')
    expect(styleCss).toContain('.page-forward-leave-to')
    expect(styleCss).toContain('.page-back-enter-from')
    expect(styleCss).toContain('.page-back-leave-to')
    expect(styleCss).toMatch(/\.page-forward-enter-from[\s\S]*?translateY/)
    expect(styleCss).toMatch(/\.page-back-enter-from[\s\S]*?translateY/)
  })

  it('respects prefers-reduced-motion', () => {
    expect(styleCss).toContain('prefers-reduced-motion')
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
})

describe('App.vue page transition', () => {
  it('wraps router-view in dynamic Transition with out-in mode', () => {
    expect(appVue).toContain(':name="transitionName"')
    expect(appVue).toContain('mode="out-in"')
    expect(appVue).toContain('<router-view')
  })

  it('imports usePageTransition composable', () => {
    expect(appVue).toContain("import { usePageTransition } from './composables/usePageTransition'")
  })
})
