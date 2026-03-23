import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppModal from '../AppModal.vue'

describe('AppModal', () => {
  const mountModal = (props = {}, slots = {}) =>
    mount(AppModal, {
      props: { open: true, ...props },
      slots: { default: 'Modal content', ...slots },
      global: { stubs: { Teleport: true } },
    })

  it('renders content when open', () => {
    const wrapper = mountModal()
    expect(wrapper.text()).toContain('Modal content')
  })

  it('does not render content when closed', () => {
    const wrapper = mountModal({ open: false })
    expect(wrapper.text()).not.toContain('Modal content')
  })

  it('renders title', () => {
    const wrapper = mountModal({ title: 'My Dialog' })
    expect(wrapper.find('h2').text()).toBe('My Dialog')
  })

  it('renders close button', () => {
    const wrapper = mountModal({ title: 'Test' })
    expect(wrapper.find('button[aria-label="Close"]').exists()).toBe(true)
  })

  it('emits close on close button click', async () => {
    const wrapper = mountModal({ title: 'Test' })
    await wrapper.find('button[aria-label="Close"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close on backdrop click', async () => {
    const wrapper = mountModal()
    await wrapper.find('.fixed').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('does not emit close when clicking inside dialog', async () => {
    const wrapper = mountModal()
    await wrapper.find('.bg-\\[--color-surface\\]').trigger('click')
    expect(wrapper.emitted('close')).toBeUndefined()
  })

  it('renders footer slot', () => {
    const wrapper = mountModal({}, { footer: 'Footer content' })
    expect(wrapper.text()).toContain('Footer content')
  })
})
