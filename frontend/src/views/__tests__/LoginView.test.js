import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import LoginView from '../LoginView.vue'

function createTestRouter(initialRoute = '/login') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: LoginView },
      { path: '/', name: 'landing', component: { template: '<div>Home</div>' } },
    ],
  })
  router.push(initialRoute)
  return router
}

function mountLoginView(router, pinia) {
  return mount(LoginView, {
    global: {
      plugins: [pinia, router],
    },
  })
}

describe('LoginView', () => {
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.restoreAllMocks()
  })

  it('renders the sign-in heading', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    expect(wrapper.find('h2').text()).toBe('Sign in to MiroFish Demo')
  })

  it('renders the domain restriction notice', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    expect(wrapper.text()).toContain('Restricted to @intercom.io accounts')
  })

  it('renders Google and Okta buttons by default', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(2)
    expect(buttons[0].text()).toContain('Continue with Google')
    expect(buttons[1].text()).toContain('Continue with Okta SSO')
  })

  it('calls loginWithGoogle when Google button is clicked', async () => {
    delete window.location
    window.location = { href: '' }

    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    await wrapper.findAll('button')[0].trigger('click')
    expect(window.location.href).toBe('/api/auth/google')
  })

  it('calls loginWithOkta when Okta button is clicked', async () => {
    delete window.location
    window.location = { href: '' }

    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    await wrapper.findAll('button')[1].trigger('click')
    expect(window.location.href).toBe('/api/auth/okta')
  })

  it('fetches user on callback and redirects to home on success', async () => {
    const mockUser = { email: 'test@intercom.io', name: 'Test' }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUser),
    })

    const router = createTestRouter('/login?callback=true')
    await router.isReady()
    mountLoginView(router, pinia)

    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('shows error when callback auth fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false })

    const router = createTestRouter('/login?callback=true')
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    await flushPromises()
    expect(wrapper.text()).toContain('Sign-in failed')
  })

  it('uses dark navy background', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    const outerDiv = wrapper.find('div')
    expect(outerDiv.classes()).toContain('bg-[var(--color-navy)]')
  })
})
