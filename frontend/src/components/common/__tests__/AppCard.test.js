import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppCard from '../AppCard.vue'

describe('AppCard', () => {
  it('renders default slot content', () => {
    const wrapper = mount(AppCard, { slots: { default: 'Card body' } })
    expect(wrapper.text()).toBe('Card body')
  })

  it('has white bg, border, and rounded-lg classes', () => {
    const wrapper = mount(AppCard)
    expect(wrapper.classes()).toContain('bg-[--color-surface]')
    expect(wrapper.classes()).toContain('border')
    expect(wrapper.classes()).toContain('border-[--color-border]')
    expect(wrapper.classes()).toContain('rounded-lg')
  })

  it('applies padding by default', () => {
    const wrapper = mount(AppCard)
    expect(wrapper.classes()).toContain('p-6')
  })

  it('removes padding when padding is false', () => {
    const wrapper = mount(AppCard, { props: { padding: false } })
    expect(wrapper.classes()).not.toContain('p-6')
  })

  it('renders header slot', () => {
    const wrapper = mount(AppCard, {
      slots: { header: '<h3>Title</h3>', default: 'Body' },
    })
    expect(wrapper.find('h3').text()).toBe('Title')
  })

  it('does not render header container when no header slot', () => {
    const wrapper = mount(AppCard, { slots: { default: 'Body' } })
    expect(wrapper.find('.mb-4').exists()).toBe(false)
  })
})
