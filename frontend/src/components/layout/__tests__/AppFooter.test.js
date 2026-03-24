import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppFooter from '../AppFooter.vue'

describe('AppFooter', () => {
  it('renders "Powered by MiroFish" attribution', () => {
    const wrapper = mount(AppFooter)
    expect(wrapper.text()).toContain('Powered by')
    expect(wrapper.text()).toContain('MiroFish')
  })

  it('renders the Swarm Intelligence Engine tagline', () => {
    const wrapper = mount(AppFooter)
    expect(wrapper.text()).toContain('Swarm Intelligence Engine')
  })

  it('renders the Intercom GTM Systems credit', () => {
    const wrapper = mount(AppFooter)
    expect(wrapper.text()).toContain('Intercom GTM Systems')
  })

  it('links to the MiroFish GitHub repository', () => {
    const wrapper = mount(AppFooter)
    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://github.com/666ghj/MiroFish')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toContain('noopener')
  })

  it('renders the current year', () => {
    const wrapper = mount(AppFooter)
    const year = new Date().getFullYear().toString()
    expect(wrapper.text()).toContain(year)
  })

  it('uses a <footer> element', () => {
    const wrapper = mount(AppFooter)
    expect(wrapper.element.tagName).toBe('FOOTER')
  })
})
