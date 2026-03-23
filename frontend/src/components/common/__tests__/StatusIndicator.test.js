import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusIndicator from '../StatusIndicator.vue'

describe('StatusIndicator', () => {
  it('renders running status with green dot', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'running' } })
    expect(wrapper.find('.bg-green-500').exists()).toBe(true)
    expect(wrapper.text()).toContain('Running')
  })

  it('renders complete status with primary dot', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'complete' } })
    expect(wrapper.find('.bg-\\[--color-primary\\]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Complete')
  })

  it('renders error status with red dot', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'error' } })
    expect(wrapper.find('.bg-red-500').exists()).toBe(true)
    expect(wrapper.text()).toContain('Error')
  })

  it('shows animate-ping for running status', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'running' } })
    expect(wrapper.find('.animate-ping').exists()).toBe(true)
  })

  it('does not animate for complete status', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'complete' } })
    expect(wrapper.find('.animate-ping').exists()).toBe(false)
  })

  it('does not animate for error status', () => {
    const wrapper = mount(StatusIndicator, { props: { status: 'error' } })
    expect(wrapper.find('.animate-ping').exists()).toBe(false)
  })

  it('uses custom label when provided', () => {
    const wrapper = mount(StatusIndicator, {
      props: { status: 'running', label: 'In Progress' },
    })
    expect(wrapper.text()).toContain('In Progress')
    expect(wrapper.text()).not.toContain('Running')
  })
})
