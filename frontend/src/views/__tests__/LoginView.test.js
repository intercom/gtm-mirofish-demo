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

  it('renders email input and Continue button', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    const emailInput = wrapper.find('input[type="email"]')
    expect(emailInput.exists()).toBe(true)
    expect(emailInput.attributes('placeholder')).toBe('you@intercom.io')

    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(1)
    expect(buttons[0].text()).toBe('Continue')
  })

  it('shows error when submitting empty email', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('Please enter your email address.')
  })

  it('shows error when email domain is not allowed', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    await wrapper.find('input[type="email"]').setValue('user@gmail.com')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('Only @intercom.io accounts are allowed.')
  })

  it('redirects to home on valid email login', async () => {
    const router = createTestRouter()
    await router.isReady()
    const wrapper = mountLoginView(router, pinia)

    await wrapper.find('input[type="email"]').setValue('test@intercom.io')
    await wrapper.find('form').trigger('submit')
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
