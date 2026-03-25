import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import SettingsView from '../SettingsView.vue'

const themePreference = ref('system')
vi.mock('../../composables/useTheme', () => ({
  useTheme: () => ({
    preference: themePreference,
    isDark: { value: false },
    setTheme: vi.fn((v) => { themePreference.value = v }),
  }),
}))

function mountSettings(opts = {}) {
  return mount(SettingsView, {
    global: {
      stubs: { 'router-link': { template: '<a><slot /></a>' } },
    },
    ...opts,
  })
}

describe('SettingsView', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('renders all four section headings', () => {
    const wrapper = mountSettings()
    const headings = wrapper.findAll('h2').map((h) => h.text())
    expect(headings).toContain('LLM Provider')
    expect(headings).toContain('Zep Cloud (Knowledge Graph)')
    expect(headings).toContain('Simulation Defaults')
  })

  it('renders three LLM provider radio buttons', () => {
    const wrapper = mountSettings()
    const radios = wrapper.findAll('input[type="radio"]')
    expect(radios).toHaveLength(3)
  })

  it('selects anthropic provider by default', () => {
    const wrapper = mountSettings()
    const selected = wrapper.findAll('input[type="radio"]').find(r => r.element.checked)
    expect(selected.element.value).toBe('anthropic')
  })

  it('renders API key inputs for LLM and Zep', () => {
    const wrapper = mountSettings()
    const passwords = wrapper.findAll('input[type="password"]')
    expect(passwords).toHaveLength(2)
  })

  it('renders Test Connection buttons for LLM and Zep', () => {
    const wrapper = mountSettings()
    const buttons = wrapper.findAll('button')
    const testButtons = buttons.filter((b) => b.text().includes('Test Connection'))
    expect(testButtons).toHaveLength(2)
  })

  it('disables Test Connection when API key is empty', () => {
    const wrapper = mountSettings()
    const testButtons = wrapper.findAll('button').filter((b) => b.text().includes('Test Connection'))
    testButtons.forEach((btn) => {
      expect(btn.attributes('disabled')).toBeDefined()
    })
  })

  it('renders simulation defaults: range slider, duration buttons, platform buttons', () => {
    const wrapper = mountSettings()
    expect(wrapper.find('input[type="range"]').exists()).toBe(true)
    const durationButtons = wrapper.findAll('button').filter(b => /^\d+ hours/.test(b.text()))
    expect(durationButtons).toHaveLength(3)
    const platformButtons = wrapper.findAll('button').filter((b) =>
      ['Twitter', 'Reddit', 'Both'].includes(b.text())
    )
    expect(platformButtons).toHaveLength(3)
  })

  it('defaults to agentCount=200, duration=72, platform=parallel', () => {
    const wrapper = mountSettings()
    expect(wrapper.find('input[type="range"]').element.value).toBe('200')
    const btn72 = wrapper.findAll('button').find(b => b.text() === '72 hours (recommended)')
    expect(btn72.classes().join(' ')).toContain('text-white')
    const bothBtn = wrapper.findAll('button').find((b) => b.text() === 'Both')
    expect(bothBtn.classes().join(' ')).toContain('text-white')
  })

  it('persists settings to localStorage on change', async () => {
    const wrapper = mountSettings()
    const radios = wrapper.findAll('input[type="radio"]')
    await radios[1].setValue(true) // select openai
    await wrapper.vm.$nextTick()

    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved.provider).toBe('openai')
  })

  it('loads saved settings from localStorage', async () => {
    localStorage.setItem('mirofish-settings', JSON.stringify({
      provider: 'gemini',
      apiKey: 'test-key-123',
      zepKey: 'zep-key-456',
      agentCount: 100,
      duration: 48,
      platformMode: 'reddit',
    }))

    const wrapper = mountSettings()
    await wrapper.vm.$nextTick()

    const selectedRadio = wrapper.find('input[type="radio"][value="gemini"]')
    expect(selectedRadio.element.checked).toBe(true)
    expect(wrapper.find('input[type="range"]').element.value).toBe('100')
    const btn48 = wrapper.findAll('button').find(b => b.text() === '48 hours')
    expect(btn48.classes().join(' ')).toContain('text-white')
  })

  it('hides auth section when auth is not enabled', () => {
    const wrapper = mountSettings()
    const headings = wrapper.findAll('h2').map((h) => h.text())
    expect(headings).not.toContain('Authentication')
  })

  it('calls test-llm endpoint when clicking Test Connection for LLM', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ ok: true }),
    })

    const wrapper = mountSettings()
    await wrapper.findAll('input[type="password"]')[0].setValue('sk-test')
    await wrapper.vm.$nextTick()

    const testBtn = wrapper.findAll('button').find((b) => b.text().includes('Test Connection'))
    await testBtn.trigger('click')

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/settings/test-llm'),
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('shows error message when test connection fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ ok: false, error: 'Invalid API key' }),
    })

    const wrapper = mountSettings()
    await wrapper.findAll('input[type="password"]')[0].setValue('bad-key')
    await wrapper.vm.$nextTick()

    const testBtn = wrapper.findAll('button').find((b) => b.text().includes('Test Connection'))
    await testBtn.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Invalid API key')
  })
})
