import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import AppNav from '../components/layout/AppNav.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import ChatView from '../views/ChatView.vue'
import SettingsView from '../views/SettingsView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/settings', component: { template: '<div />' } },
      { path: '/scenarios/:id', component: { template: '<div />' } },
      { path: '/chat/:taskId', component: { template: '<div />' } },
      { path: '/report/:taskId', component: { template: '<div />' } },
      { path: '/simulation/:taskId', component: { template: '<div />' } },
    ],
  })
}

async function mountWithRouter(component, options = {}) {
  const router = createTestRouter()
  const pinia = createPinia()
  router.push('/')
  await router.isReady()
  return mount(component, {
    global: { plugins: [router, pinia] },
    ...options,
  })
}

describe('AppNav — hamburger menu', () => {
  it('renders hamburger button with md:hidden class', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')
    expect(hamburger.exists()).toBe(true)
    expect(hamburger.classes()).toContain('md:hidden')
  })

  it('hides desktop nav links on mobile via hidden md:flex', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const desktopNav = wrapper.find('.hidden.md\\:flex')
    expect(desktopNav.exists()).toBe(true)
  })

  it('mobile menu is hidden by default', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const mobileMenu = wrapper.find('.md\\:hidden.absolute')
    expect(mobileMenu.exists()).toBe(false)
  })

  it('toggles mobile menu on hamburger click', async () => {
    const wrapper = await mountWithRouter(AppNav)
    const hamburger = wrapper.find('button[aria-label="Toggle navigation menu"]')

    await hamburger.trigger('click')
    let mobileMenu = wrapper.find('.md\\:hidden.absolute')
    expect(mobileMenu.exists()).toBe(true)

    const links = mobileMenu.findAll('a')
    expect(links.length).toBeGreaterThanOrEqual(2)

    await hamburger.trigger('click')
    mobileMenu = wrapper.find('.md\\:hidden.absolute')
    expect(mobileMenu.exists()).toBe(false)
  })
})

describe('ChatView — mobile layout adjustments', () => {
  it('has responsive input padding', async () => {
    const wrapper = await mountWithRouter(ChatView, {
      props: { taskId: 'test-123' },
    })
    const inputArea = wrapper.find('.border-t')
    expect(inputArea.classes()).toContain('px-4')
    expect(inputArea.classes()).toContain('md:px-6')
  })
})

describe('SettingsView — mobile layout', () => {
  it('API key inputs stack on mobile with flex-col sm:flex-row', async () => {
    const wrapper = await mountWithRouter(SettingsView)
    const inputGroups = wrapper.findAll('.flex.flex-col.sm\\:flex-row')
    expect(inputGroups.length).toBeGreaterThanOrEqual(2)
  })

  it('has responsive page padding', async () => {
    const wrapper = await mountWithRouter(SettingsView)
    const container = wrapper.find('.max-w-2xl')
    expect(container.classes()).toContain('px-4')
    expect(container.classes()).toContain('md:px-6')
  })
})

describe('AppFooter — mobile layout', () => {
  it('breaks footer text on mobile with sm:hidden br', async () => {
    const router = createTestRouter()
    router.push('/')
    await router.isReady()
    const wrapper = mount(AppFooter, { global: { plugins: [router] } })

    const br = wrapper.find('br')
    expect(br.exists()).toBe(true)
    expect(br.classes()).toContain('sm:hidden')
  })
})
