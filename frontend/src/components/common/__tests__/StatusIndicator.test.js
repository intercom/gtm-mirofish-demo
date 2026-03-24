import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusIndicator from '../StatusIndicator.vue'

describe('StatusIndicator', () => {
  it('renders with idle status by default', () => {
    const wrapper = mount(StatusIndicator)
    const dot = wrapper.find('.rounded-full')
    expect(dot.classes()).toContain('bg-[var(--color-text-muted)]')
    expect(wrapper.text()).toBe('idle')
  })

  it('shows green pulsing dot for running status', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'running' } })
    const dot = wrapper.find('.rounded-full')
    expect(dot.classes()).toContain('bg-[var(--color-success)]')
    expect(dot.classes()).toContain('animate-pulse')
  })

  it('shows primary-colored dot for complete status', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'complete' } })
    const dot = wrapper.find('.rounded-full')
    expect(dot.classes()).toContain('bg-[var(--color-primary)]')
  })

  it('shows error-colored dot for error status', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'error' } })
    const dot = wrapper.find('.rounded-full')
    expect(dot.classes()).toContain('bg-[var(--color-error)]')
  })

  it('renders custom slot content instead of default label', () => {
    const wrapper = mount(StatusIndicator, {
      props: { status: 'running' },
      slots: { default: 'Processing...' },
    })
    expect(wrapper.text()).toBe('Processing...')
  })
})
