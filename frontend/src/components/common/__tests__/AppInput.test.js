import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AppInput from '../AppInput.vue'

describe('AppInput', () => {
  it('renders a text input by default', () => {
    const wrapper = mount(AppInput)
    expect(wrapper.find('input[type="text"]').exists()).toBe(true)
  })

  it('renders a textarea when type is textarea', () => {
    const wrapper = mount(AppInput, { props: { type: 'textarea' } })
    expect(wrapper.find('textarea').exists()).toBe(true)
  })

  it('renders a select when type is select', () => {
    const wrapper = mount(AppInput, {
      props: { type: 'select', options: ['A', 'B'] },
    })
    expect(wrapper.find('select').exists()).toBe(true)
    expect(wrapper.findAll('option')).toHaveLength(2)
  })

  it('renders label when provided', () => {
    const wrapper = mount(AppInput, { props: { label: 'Name' } })
    expect(wrapper.find('label').text()).toBe('Name')
  })

  it('does not render label when not provided', () => {
    const wrapper = mount(AppInput)
    expect(wrapper.find('label').exists()).toBe(false)
  })

  it('emits update:modelValue on text input', async () => {
    const wrapper = mount(AppInput, { props: { modelValue: '' } })
    await wrapper.find('input').setValue('hello')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['hello'])
  })

  it('emits update:modelValue on textarea input', async () => {
    const wrapper = mount(AppInput, {
      props: { type: 'textarea', modelValue: '' },
    })
    await wrapper.find('textarea').setValue('text')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['text'])
  })

  it('emits update:modelValue on select change', async () => {
    const wrapper = mount(AppInput, {
      props: { type: 'select', options: ['A', 'B'], modelValue: 'A' },
    })
    await wrapper.find('select').setValue('B')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['B'])
  })

  it('shows error message', () => {
    const wrapper = mount(AppInput, { props: { error: 'Required' } })
    expect(wrapper.find('.text-red-500').text()).toBe('Required')
  })

  it('applies error border class', () => {
    const wrapper = mount(AppInput, { props: { error: 'Required' } })
    expect(wrapper.find('input').classes()).toContain('border-red-500')
  })

  it('renders placeholder text on select', () => {
    const wrapper = mount(AppInput, {
      props: { type: 'select', options: ['A'], placeholder: 'Pick one' },
    })
    const opts = wrapper.findAll('option')
    expect(opts[0].text()).toBe('Pick one')
    expect(opts[0].attributes('disabled')).toBeDefined()
  })

  it('supports object options with value/label', () => {
    const wrapper = mount(AppInput, {
      props: {
        type: 'select',
        options: [
          { value: '1', label: 'One' },
          { value: '2', label: 'Two' },
        ],
      },
    })
    const opts = wrapper.findAll('option')
    expect(opts[0].text()).toBe('One')
    expect(opts[0].attributes('value')).toBe('1')
  })

  it('applies custom rows to textarea', () => {
    const wrapper = mount(AppInput, {
      props: { type: 'textarea', rows: 8 },
    })
    expect(wrapper.find('textarea').attributes('rows')).toBe('8')
  })
})
