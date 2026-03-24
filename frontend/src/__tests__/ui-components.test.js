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

  it('hides label when empty string', () => {
    const wrapper = mount(LoadingSpinner, { props: { label: '' } })
    expect(wrapper.find('p').exists()).toBe(false)
  })

  it('renders spinner element with animate-spin', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })

  it('applies size classes', () => {
    const sm = mount(LoadingSpinner, { props: { size: 'sm' } })
    expect(sm.find('.w-5').exists()).toBe(true)

    const lg = mount(LoadingSpinner, { props: { size: 'lg' } })
    expect(lg.find('.w-12').exists()).toBe(true)
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

  it('renders default title and message', () => {
    const wrapper = mount(ErrorState)
    expect(wrapper.text()).toContain('Something went wrong')
  })

  it('renders custom error message', () => {
    const wrapper = mount(ErrorState, { props: { message: 'Network error' } })
    expect(wrapper.text()).toContain('Network error')
  })

  it('renders retry button with default label', () => {
    const wrapper = mount(ErrorState)
    expect(wrapper.find('button').text()).toContain('Try Again')
  })

  it('renders retry button with custom label', () => {
    const wrapper = mount(ErrorState, { props: { retryLabel: 'Reload' } })
    expect(wrapper.find('button').text()).toContain('Reload')
  })

  it('emits retry event on button click', async () => {
    const wrapper = mount(ErrorState)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})

describe('EmptyState', () => {
  it('renders with default props', () => {
    const wrapper = mount(EmptyState)
    expect(wrapper.text()).toContain('Nothing here yet')
    expect(wrapper.text()).toContain('📭')
  })

  it('renders title, description, and icon', () => {
    const wrapper = mount(EmptyState, {
      props: { title: 'No data', description: 'Nothing here', icon: '📭' },
    })
    expect(wrapper.text()).toContain('No data')
    expect(wrapper.text()).toContain('Nothing here')
    expect(wrapper.text()).toContain('📭')
  })

  it('renders custom icon and title', () => {
    const wrapper = mount(EmptyState, { props: { icon: '🐟', title: 'No fish' } })
    expect(wrapper.text()).toContain('🐟')
    expect(wrapper.text()).toContain('No fish')
  })

  it('renders description when provided', () => {
    const wrapper = mount(EmptyState, { props: { description: 'Try adding something' } })
    expect(wrapper.text()).toContain('Try adding something')
  })

  it('renders action button when actionLabel provided', () => {
    const wrapper = mount(EmptyState, {
      props: { actionLabel: 'Create one' },
    })
    expect(wrapper.find('button').text()).toBe('Create one')
  })

  it('renders action button and emits action event', async () => {
    const wrapper = mount(EmptyState, { props: { actionLabel: 'Add Item' } })
    const btn = wrapper.find('button')
    expect(btn.text()).toBe('Add Item')
    await btn.trigger('click')
    expect(wrapper.emitted('action')).toHaveLength(1)
  })

  it('renders router-link when actionTo provided', () => {
    const wrapper = mount(EmptyState, {
      props: { actionLabel: 'Go home', actionTo: '/' },
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>', props: ['to'] } },
      },
    })
    expect(wrapper.find('a').text()).toBe('Go home')
  })

  it('hides action when no actionLabel', () => {
    const wrapper = mount(EmptyState)
    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.find('a').exists()).toBe(false)
  })
})
