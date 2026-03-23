import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Modal from '../Modal.vue'

describe('Modal', () => {
  const mountModal = (props = {}, slots = {}) =>
    mount(Modal, {
      props: { open: true, ...props },
      slots: { default: 'Modal body', ...slots },
      global: { stubs: { Teleport: true, Transition: true } },
    })

  it('renders when open is true', () => {
    const wrapper = mountModal()
    expect(wrapper.text()).toContain('Modal body')
  })

  it('does not render content when open is false', () => {
    const wrapper = mount(Modal, {
      props: { open: false },
      slots: { default: 'Hidden' },
      global: { stubs: { Teleport: true, Transition: true } },
    })
    expect(wrapper.text()).not.toContain('Hidden')
  })

  it('renders title when provided', () => {
    const wrapper = mountModal({ title: 'My Dialog' })
    expect(wrapper.text()).toContain('My Dialog')
  })

  it('uses token-based surface color on dialog panel', () => {
    const wrapper = mountModal({ title: 'Test' })
    const panel = wrapper.find('.bg-\\[var\\(--color-surface\\)\\]')
    expect(panel.exists()).toBe(true)
  })

  it('emits close when close button is clicked', async () => {
    const wrapper = mountModal({ title: 'Test' })
    await wrapper.find('button[aria-label="Close"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close when overlay is clicked', async () => {
    const wrapper = mountModal({ title: 'Test' })
    const overlay = wrapper.find('.fixed')
    await overlay.trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('renders footer slot when provided', () => {
    const wrapper = mountModal({}, { footer: '<button>Save</button>' })
    expect(wrapper.text()).toContain('Save')
  })
})
