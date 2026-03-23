import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import EmptyState from '../components/ui/EmptyState.vue'

describe('LoadingSpinner', () => {
  it('renders with default label', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.text()).toContain('Loading...')
  })

  it('renders with custom label', () => {
    const wrapper = mount(LoadingSpinner, { props: { label: 'Building graph...' } })
    expect(wrapper.text()).toContain('Building graph...')
  })

  it('has accessible role=status', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('[role="status"]').exists()).toBe(true)
  })
})

describe('ErrorState', () => {
  it('renders title and message', () => {
    const wrapper = mount(ErrorState, {
      props: { title: 'Oops', message: 'Server error' },
    })
    expect(wrapper.text()).toContain('Oops')
    expect(wrapper.text()).toContain('Server error')
  })

  it('emits retry on button click', async () => {
    const wrapper = mount(ErrorState)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})

describe('EmptyState', () => {
  it('renders title, description, and icon', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No data', description: 'Nothing here', icon: '📭' },
    })
    expect(wrapper.text()).toContain('No data')
    expect(wrapper.text()).toContain('Nothing here')
    expect(wrapper.text()).toContain('📭')
  })

  it('renders action button when actionLabel provided', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'Empty', actionLabel: 'Create one' },
    })
    expect(wrapper.find('button').text()).toBe('Create one')
  })

  it('renders router-link when actionTo provided', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'Empty', actionLabel: 'Go home', actionTo: '/' },
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>', props: ['to'] } },
      },
    })
    expect(wrapper.find('a').text()).toBe('Go home')
  })

  it('emits action event on button click', async () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'Empty', actionLabel: 'Do something' },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('action')).toHaveLength(1)
  })
})
