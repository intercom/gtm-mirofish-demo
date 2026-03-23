import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppButton from '../AppButton.vue'

describe('AppButton', () => {
  it('renders slot content', () => {
    const wrapper = mount(AppButton, { slots: { default: 'Click me' } })
    expect(wrapper.text()).toBe('Click me')
  })

  it('applies primary variant classes by default', () => {
    const wrapper = mount(AppButton)
    expect(wrapper.classes()).toContain('bg-[--color-primary]')
  })

  it('applies secondary variant classes', () => {
    const wrapper = mount(AppButton, { props: { variant: 'secondary' } })
    expect(wrapper.classes()).toContain('border')
    expect(wrapper.classes()).toContain('border-[--color-primary-border]')
  })

  it('applies ghost variant classes', () => {
    const wrapper = mount(AppButton, { props: { variant: 'ghost' } })
    expect(wrapper.classes()).toContain('text-[--color-text-secondary]')
  })

  it('applies size sm classes', () => {
    const wrapper = mount(AppButton, { props: { size: 'sm' } })
    expect(wrapper.classes()).toContain('text-xs')
    expect(wrapper.classes()).toContain('px-3')
  })

  it('applies size md classes by default', () => {
    const wrapper = mount(AppButton)
    expect(wrapper.classes()).toContain('text-sm')
    expect(wrapper.classes()).toContain('px-5')
  })

  it('applies size lg classes', () => {
    const wrapper = mount(AppButton, { props: { size: 'lg' } })
    expect(wrapper.classes()).toContain('px-8')
    expect(wrapper.classes()).toContain('py-3')
  })

  it('disables button when disabled prop is true', () => {
    const wrapper = mount(AppButton, { props: { disabled: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('disables button when loading prop is true', () => {
    const wrapper = mount(AppButton, { props: { loading: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('shows spinner when loading', () => {
    const wrapper = mount(AppButton, { props: { loading: true } })
    expect(wrapper.find('svg.animate-spin').exists()).toBe(true)
  })

  it('hides spinner when not loading', () => {
    const wrapper = mount(AppButton)
    expect(wrapper.find('svg.animate-spin').exists()).toBe(false)
  })

  it('emits click event', async () => {
    const wrapper = mount(AppButton)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })
})
