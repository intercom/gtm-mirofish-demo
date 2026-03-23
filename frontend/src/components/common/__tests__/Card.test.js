import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Card from '../Card.vue'

describe('Card', () => {
  it('renders slot content', () => {
    const wrapper = mount(Card, { slots: { default: '<p>Card content</p>' } })
    expect(wrapper.text()).toBe('Card content')
  })

  it('has white bg and subtle border', () => {
    const wrapper = mount(Card)
    expect(wrapper.classes()).toContain('bg-white')
    expect(wrapper.classes()).toContain('border')
    expect(wrapper.classes()).toContain('border-black/10')
    expect(wrapper.classes()).toContain('rounded-lg')
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
