import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const styleCss = readFileSync(resolve(__dirname, '../style.css'), 'utf-8')
const appVue = readFileSync(resolve(__dirname, '../App.vue'), 'utf-8')

describe('Transition CSS classes', () => {
  it('defines page-enter-active and page-leave-active classes', () => {
    expect(styleCss).toContain('.page-enter-active')
    expect(styleCss).toContain('.page-leave-active')
  })

  it('page transition uses fade + slide transform', () => {
    expect(styleCss).toContain('.page-enter-from')
    expect(styleCss).toContain('.page-leave-to')
    expect(styleCss).toMatch(/\.page-enter-from[\s\S]*?translateY/)
    expect(styleCss).toMatch(/\.page-leave-to[\s\S]*?translateY/)
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

  it('defines card-list transition for staggered grids', () => {
    expect(styleCss).toContain('.card-list-enter-active')
    expect(styleCss).toContain('.card-list-enter-from')
  })

  it('uses brand token transition durations', () => {
    expect(styleCss).toContain('var(--transition-base)')
    expect(styleCss).toContain('var(--transition-slow)')
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
  it('wraps router-view in Transition with name="page"', () => {
    expect(appVue).toContain('<Transition name="page" mode="out-in">')
    expect(appVue).toContain('<router-view')
  })
})
