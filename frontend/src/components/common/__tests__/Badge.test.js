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
    expect(wrapper.classes()).toContain('text-[var(--color-text-secondary)]')
  })

  it('applies primary variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'primary' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-primary-bg)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-primary-text)]')
  })

  it('applies success variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'success' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-success-bg-soft)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-success-text-soft)]')
  })

  it('applies warning variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'warning' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-warning-bg-soft)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-warning-text-soft)]')
  })

  it('applies error variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'error' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-error-bg-soft)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-error-text-soft)]')
  })

  it('applies info variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'info' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-secondary-bg)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-secondary-text)]')
  })

  it('applies orange variant classes', () => {
    const wrapper = mount(Badge, { props: { variant: 'orange' } })
    expect(wrapper.classes()).toContain('bg-[var(--badge-orange-bg-soft)]')
    expect(wrapper.classes()).toContain('text-[var(--badge-orange-text-soft)]')
  })

  it('always has rounded-full', () => {
    const wrapper = mount(Badge)
    expect(wrapper.classes()).toContain('rounded-full')
  })

  it('uses token-based sizing via inline style', () => {
    const wrapper = mount(Badge)
    expect(wrapper.attributes('style')).toContain('font-size')
    expect(wrapper.attributes('style')).toContain('padding')
  })
})
