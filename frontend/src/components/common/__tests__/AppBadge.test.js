import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppBadge from '../AppBadge.vue'

describe('AppBadge', () => {
  it('renders slot content', () => {
    const wrapper = mount(AppBadge, { slots: { default: 'Active' } })
    expect(wrapper.text()).toBe('Active')
  })

  it('applies neutral variant by default', () => {
    const wrapper = mount(AppBadge)
    expect(wrapper.classes()).toContain('bg-black/5')
    expect(wrapper.classes()).toContain('text-[--color-text-secondary]')
  })

  it('applies primary variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'primary' } })
    expect(wrapper.classes()).toContain('text-[--color-primary]')
  })

  it('applies success variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'success' } })
    expect(wrapper.classes()).toContain('bg-green-100')
    expect(wrapper.classes()).toContain('text-green-700')
  })

  it('applies warning variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'warning' } })
    expect(wrapper.classes()).toContain('text-[--color-fin-orange]')
  })

  it('applies error variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'error' } })
    expect(wrapper.classes()).toContain('bg-red-100')
    expect(wrapper.classes()).toContain('text-red-700')
  })

  it('has rounded-full pill shape', () => {
    const wrapper = mount(AppBadge)
    expect(wrapper.classes()).toContain('rounded-full')
  })
})
