import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Input from '../Input.vue'

describe('Input', () => {
  it('renders a text input by default', () => {
    const wrapper = mount(Input)
    expect(wrapper.find('input').exists()).toBe(true)
    expect(wrapper.find('input').attributes('type')).toBe('text')
  })

  it('renders a textarea when type=textarea', () => {
    const wrapper = mount(Input, { props: { type: 'textarea' } })
    expect(wrapper.find('textarea').exists()).toBe(true)
  })

  it('renders a select when type=select', () => {
    const wrapper = mount(Input, {
      props: {
        type: 'select',
        options: [{ value: 'a', label: 'Option A' }, { value: 'b', label: 'Option B' }],
      },
    })
    expect(wrapper.find('select').exists()).toBe(true)
    expect(wrapper.findAll('option')).toHaveLength(2)
  })

  it('applies token-based input styling classes', () => {
    const wrapper = mount(Input)
    const input = wrapper.find('input')
    expect(input.classes()).toContain('bg-[var(--input-bg)]')
    expect(input.classes()).toContain('border-[var(--input-border)]')
    expect(input.classes()).toContain('text-[var(--input-text)]')
  })

  it('renders label when provided', () => {
    const wrapper = mount(Input, { props: { label: 'Email' } })
    expect(wrapper.find('label').text()).toBe('Email')
  })

  it('does not render label when not provided', () => {
    const wrapper = mount(Input)
    expect(wrapper.find('label').exists()).toBe(false)
  })

  it('emits update:modelValue on text input', async () => {
    const wrapper = mount(Input, { props: { modelValue: '' } })
    await wrapper.find('input').setValue('hello')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['hello'])
  })

  it('emits update:modelValue on textarea input', async () => {
    const wrapper = mount(Input, { props: { type: 'textarea', modelValue: '' } })
    await wrapper.find('textarea').setValue('text content')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['text content'])
  })

  it('emits update:modelValue on select change', async () => {
    const wrapper = mount(Input, {
      props: {
        type: 'select',
        modelValue: 'a',
        options: [{ value: 'a', label: 'A' }, { value: 'b', label: 'B' }],
      },
    })
    await wrapper.find('select').setValue('b')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['b'])
  })

  it('accepts string options', () => {
    const wrapper = mount(Input, {
      props: { type: 'select', options: ['one', 'two', 'three'] },
    })
    const options = wrapper.findAll('option')
    expect(options).toHaveLength(3)
    expect(options[0].text()).toBe('one')
  })

  it('sets placeholder on select', () => {
    const wrapper = mount(Input, {
      props: { type: 'select', placeholder: 'Choose...', options: ['a'] },
    })
    const placeholderOpt = wrapper.findAll('option')[0]
    expect(placeholderOpt.text()).toBe('Choose...')
    expect(placeholderOpt.attributes('disabled')).toBeDefined()
  })

  it('disables the input', () => {
    const wrapper = mount(Input, { props: { disabled: true } })
    expect(wrapper.find('input').attributes('disabled')).toBeDefined()
  })
})
