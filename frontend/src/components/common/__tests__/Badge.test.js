import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Badge from '../Badge.vue'

describe('Badge', () => {
  it('renders slot content', () => {
    const wrapper = mount(Badge, { slots: { default: 'Active' } })
    expect(wrapper.text()).toBe('Active')
  })

  it('applies default variant classes', () => {
    const wrapper = mount(Badge)
    expect(wrapper.classes()).toContain('bg-black/5')
    expect(wrapper.classes()).toContain('text-[#555]')
  })

  it('applies success variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'success' } })
    expect(wrapper.classes()).toContain('bg-green-100')
    expect(wrapper.classes()).toContain('text-green-700')
  })

  it('applies warning variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'warning' } })
    expect(wrapper.classes()).toContain('bg-yellow-100')
    expect(wrapper.classes()).toContain('text-yellow-700')
  })

  it('applies error variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'error' } })
    expect(wrapper.classes()).toContain('bg-red-100')
    expect(wrapper.classes()).toContain('text-red-700')
  })

  it('applies info variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'info' } })
    expect(wrapper.classes()).toContain('bg-blue-100')
    expect(wrapper.classes()).toContain('text-blue-700')
  })

  it('always has rounded-full and text-xs', () => {
    const wrapper = mount(Badge)
    expect(wrapper.classes()).toContain('rounded-full')
    expect(wrapper.classes()).toContain('text-xs')
  })
})
