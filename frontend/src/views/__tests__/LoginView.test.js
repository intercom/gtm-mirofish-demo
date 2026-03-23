import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { setActivePinia, createPinia } from 'pinia'
import LoginView from '../LoginView.vue'
import { useAuthStore } from '../../stores/auth'

const mockPush = vi.fn()
const mockReplace = vi.fn()
let mockQuery = {}

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useRoute: () => ({ query: mockQuery }),
}))

function mountLogin(query = {}) {
  mockQuery = query
  return mount(LoginView)
}

describe('LoginView', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    mockPush.mockClear()
    mockReplace.mockClear()
    mockQuery = {}
    delete window.location
    window.location = { href: '' }
  })

  it('renders the sign-in heading', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('h2').text()).toBe('Sign in to MiroFish Demo')
  })

  it('renders the domain restriction notice', () => {
    const wrapper = mountLogin()
    expect(wrapper.text()).toContain('Restricted to @intercom.io accounts')
  })

  it('renders the Intercom logo SVG', () => {
    const wrapper = mountLogin()
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
    expect(svg.find('rect[fill="#2068FF"]').exists()).toBe(true)
  })

  it('renders Google OAuth button', () => {
    const wrapper = mountLogin()
    const btn = wrapper.find('[data-testid="google-btn"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('Continue with Google')
  })

  it('renders Okta SSO button', () => {
    const wrapper = mountLogin()
    const btn = wrapper.find('[data-testid="okta-btn"]')
    expect(btn.exists()).toBe(true)
    expect(btn.text()).toContain('Continue with Okta SSO')
  })

  it('has dark navy background', () => {
    const wrapper = mountLogin()
    const outer = wrapper.find('div')
    expect(outer.classes()).toContain('bg-[var(--color-navy)]')
  })

  it('centers the card vertically and horizontally', () => {
    const wrapper = mountLogin()
    const outer = wrapper.find('div')
    expect(outer.classes()).toContain('flex')
    expect(outer.classes()).toContain('items-center')
    expect(outer.classes()).toContain('justify-center')
  })

  it('redirects to /api/auth/google when Google button is clicked', async () => {
    const wrapper = mountLogin()
    await wrapper.find('[data-testid="google-btn"]').trigger('click')
    expect(window.location.href).toBe('/api/auth/google?redirect=%2F')
  })

  it('redirects to /api/auth/okta when Okta button is clicked', async () => {
    const wrapper = mountLogin()
    await wrapper.find('[data-testid="okta-btn"]').trigger('click')
    expect(window.location.href).toBe('/api/auth/okta?redirect=%2F')
  })

  it('passes through redirect query param to OAuth URL', async () => {
    const wrapper = mountLogin({ redirect: '/scenarios/test' })
    await wrapper.find('[data-testid="google-btn"]').trigger('click')
    expect(window.location.href).toBe('/api/auth/google?redirect=%2Fscenarios%2Ftest')
  })

  it('handles OAuth callback by storing token and user, then redirecting', () => {
    mountLogin({ token: 'abc-123', email: 'user@intercom.io', name: 'User' })
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('abc-123')
    expect(store.user).toEqual({ email: 'user@intercom.io', name: 'User' })
    expect(mockReplace).toHaveBeenCalledWith('/')
  })

  it('redirects to original path after OAuth callback', () => {
    mountLogin({ token: 'abc-123', email: 'u@intercom.io', redirect: '/settings' })
    expect(mockReplace).toHaveBeenCalledWith('/settings')
  })

  it('displays error from OAuth callback', async () => {
    const wrapper = mountLogin({ error: 'Domain not allowed' })
    await nextTick()
    expect(wrapper.find('[role="alert"]').text()).toBe('Domain not allowed')
  })

  it('does not store token when error is present', () => {
    mountLogin({ error: 'Domain not allowed' })
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
  })

  it('redirects away if already authenticated', () => {
    localStorage.setItem('auth_token', 'existing-token')
    setActivePinia(createPinia())
    mountLogin()
    expect(mockReplace).toHaveBeenCalledWith('/')
  })

  it('disables buttons while loading', async () => {
    const wrapper = mountLogin()
    await wrapper.find('[data-testid="google-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="google-btn"]').attributes('disabled')).toBeDefined()
    expect(wrapper.find('[data-testid="okta-btn"]').attributes('disabled')).toBeDefined()
  })
})
