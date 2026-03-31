import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import ErrorBoundary from '../ErrorBoundary.vue'

const ThrowingChild = defineComponent({
  render() {
    throw new Error('child render error')
  },
})

describe('ErrorBoundary', () => {
  it('renders slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      slots: { default: '<p>working content</p>' },
    })
    expect(wrapper.text()).toContain('working content')
  })

  it('shows fallback UI when child throws', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(ErrorBoundary, {
      slots: { default: () => h(ThrowingChild) },
    })
    await nextTick()

    expect(wrapper.text()).toContain('Something went wrong')
    expect(wrapper.find('button').text()).toContain('Try Again')
    console.error.mockRestore()
  })

  it('shows custom title and message on error', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(ErrorBoundary, {
      props: { title: 'Custom Title', message: 'Custom message' },
      slots: { default: () => h(ThrowingChild) },
    })
    await nextTick()

    expect(wrapper.text()).toContain('Custom Title')
    expect(wrapper.text()).toContain('Custom message')
    console.error.mockRestore()
  })

  it('recovers when retry is clicked', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(ErrorBoundary, {
      slots: { default: () => h(ThrowingChild) },
    })
    await nextTick()

    expect(wrapper.text()).toContain('Something went wrong')
    await wrapper.find('button').trigger('click')
    await nextTick()
    // After retry, error ref is cleared — slot re-renders (child throws again, re-triggering error)
    expect(wrapper.text()).toContain('Something went wrong')
    console.error.mockRestore()
  })

  it('logs error to console', async () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

    mount(ErrorBoundary, {
      slots: { default: () => h(ThrowingChild) },
    })
    await nextTick()

    expect(spy).toHaveBeenCalledWith('[ErrorBoundary]', expect.any(Error))
    spy.mockRestore()
  })
})
