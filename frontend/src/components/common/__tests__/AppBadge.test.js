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
    expect(wrapper.classes()).toContain('text-[var(--color-text-secondary)]')
  })

  it('applies primary variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'primary' } })
    expect(wrapper.classes()).toContain('text-[var(--color-primary)]')
  })

  it('applies success variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'success' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-success-bg-soft)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-success-text-soft)]')
  })

  it('applies warning variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'warning' } })
    expect(wrapper.classes()).toContain('text-[var(--badge-warning-text-soft)]')
  })

  it('applies error variant', () => {
    const wrapper = mount(AppBadge, { props: { variant: 'error' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-error-bg-soft)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-error-text-soft)]')
  })

  it('has rounded-full pill shape', () => {
    const wrapper = mount(AppBadge)
    expect(wrapper.classes()).toContain('rounded-full')
  })
})
