import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '../Button.vue'

describe('Button', () => {
  it('renders slot content', () => {
    const wrapper = mount(Button, { slots: { default: 'Click me' } })
    expect(wrapper.text()).toBe('Click me')
  })

  it('applies primary variant classes by default', () => {
    const wrapper = mount(Button)
    expect(wrapper.classes()).toContain('bg-[var(--btn-primary-bg)]')
    expect(wrapper.classes()).toContain('text-[var(--btn-primary-text)]')
  })

  it('applies secondary variant classes', () => {
    const wrapper = mount(Button, { props: { variant: 'secondary' } })
    expect(wrapper.classes()).toContain('border')
    expect(wrapper.classes()).toContain('border-[var(--btn-secondary-border)]')
    expect(wrapper.classes()).toContain('bg-[var(--btn-secondary-bg)]')
  })

  it('applies ghost variant classes', () => {
    const wrapper = mount(Button, { props: { variant: 'ghost' } })
    expect(wrapper.classes()).toContain('bg-transparent')
    expect(wrapper.classes()).toContain('text-[var(--btn-ghost-text)]')
  })

  it('applies size classes', () => {
    const sm = mount(Button, { props: { size: 'sm' } })
    expect(sm.classes()).toContain('text-xs')

    const lg = mount(Button, { props: { size: 'lg' } })
    expect(lg.classes()).toContain('px-6')
  })

  it('disables the button when disabled prop is true', () => {
    const wrapper = mount(Button, { props: { disabled: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('disables the button when loading', () => {
    const wrapper = mount(Button, { props: { loading: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('emits click event', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('sets button type attribute', () => {
    const wrapper = mount(Button, { props: { type: 'submit' } })
    expect(wrapper.attributes('type')).toBe('submit')
  })
})
