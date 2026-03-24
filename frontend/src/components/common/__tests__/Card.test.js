import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Card from '../Card.vue'

describe('Card', () => {
  it('renders slot content', () => {
    const wrapper = mount(Card, { slots: { default: '<p>Card content</p>' } })
    expect(wrapper.text()).toBe('Card content')
  })

  it('has token-based bg, border, and radius', () => {
    const wrapper = mount(Card)
    expect(wrapper.classes()).toContain('bg-[var(--card-bg)]')
    expect(wrapper.classes()).toContain('border')
    expect(wrapper.classes()).toContain('border-[var(--card-border)]')
    expect(wrapper.classes()).toContain('rounded-[var(--card-radius)]')
  })

  it('applies card shadow via inline style', () => {
    const wrapper = mount(Card)
    expect(wrapper.attributes('style')).toContain('box-shadow')
  })

  it('applies padding by default', () => {
    const wrapper = mount(Card)
    expect(wrapper.classes()).toContain('p-6')
  })

  it('removes padding when padding=false', () => {
    const wrapper = mount(Card, { props: { padding: false } })
    expect(wrapper.classes()).not.toContain('p-6')
  })
})
