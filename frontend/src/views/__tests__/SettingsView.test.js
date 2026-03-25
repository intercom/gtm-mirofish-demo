import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick, ref } from 'vue'
import SettingsView from '../SettingsView.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const themePreference = ref('system')
vi.mock('../../composables/useTheme', () => ({
  useTheme: () => ({
    preference: themePreference,
    isDark: { value: false },
    setTheme: vi.fn((v) => { themePreference.value = v }),
  }),
}))

function mountSettings() {
  return mount(SettingsView, {
    global: {
      stubs: { 'router-link': { template: '<a><slot /></a>' } },
    },
  })
}

describe('SettingsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  // ── Section rendering ──────────────────────────────────────────────

  it('renders the Settings heading', () => {
    const wrapper = mountSettings()
    expect(wrapper.find('h1').text()).toBe('Settings')
  })

  it('renders all four section headings', () => {
    const wrapper = mountSettings()
    const headings = wrapper.findAll('h2').map(h => h.text())
    expect(headings).toContain('Theme')
    expect(headings).toContain('LLM Provider')
    expect(headings).toContain('Zep Cloud (Knowledge Graph)')
    expect(headings).toContain('Simulation Defaults')
  })

  // ── LLM Provider ──────────────────────────────────────────────────

  it('renders three LLM provider radio buttons', () => {
    const wrapper = mountSettings()
    const radios = wrapper.findAll('input[type="radio"]')
    expect(radios).toHaveLength(3)
  })

  it('defaults to anthropic provider', () => {
    const wrapper = mountSettings()
    const radios = wrapper.findAll('input[type="radio"]')
    const selected = radios.find(r => r.element.checked)
    expect(selected.element.value).toBe('anthropic')
  })

  it('displays provider names and models', () => {
    const wrapper = mountSettings()
    const text = wrapper.text()
    expect(text).toContain('Claude (Anthropic)')
    expect(text).toContain('OpenAI (GPT-4o)')
    expect(text).toContain('Google Gemini')
  })

  it('renders API key input for LLM provider', () => {
    const wrapper = mountSettings()
    const passwordInputs = wrapper.findAll('input[type="password"]')
    expect(passwordInputs.length).toBeGreaterThanOrEqual(1)
  })

  it('renders Test Connection button for LLM', () => {
    const wrapper = mountSettings()
    const buttons = wrapper.findAll('button')
    const testButtons = buttons.filter(b => b.text() === 'Test Connection')
    expect(testButtons.length).toBeGreaterThanOrEqual(1)
  })

  // ── Zep Cloud ─────────────────────────────────────────────────────

  it('renders Zep API key input', () => {
    const wrapper = mountSettings()
    const inputs = wrapper.findAll('input[type="password"]')
    expect(inputs.length).toBe(2)
  })

  it('renders Zep Test Connection button', () => {
    const wrapper = mountSettings()
    const testButtons = wrapper.findAll('button').filter(b => b.text() === 'Test Connection')
    expect(testButtons).toHaveLength(2)
  })

  // ── Simulation Defaults ───────────────────────────────────────────

  it('renders agent count slider with correct defaults', () => {
    const wrapper = mountSettings()
    const slider = wrapper.find('input[type="range"]')
    expect(slider.exists()).toBe(true)
    expect(slider.element.value).toBe('200')
    expect(slider.attributes('min')).toBe('10')
    expect(slider.attributes('max')).toBe('500')
  })

  it('displays agent count value', () => {
    const wrapper = mountSettings()
    expect(wrapper.text()).toContain('200')
  })

  it('renders duration buttons for 24h, 48h, 72h', () => {
    const wrapper = mountSettings()
    const durationButtons = wrapper.findAll('button').filter(b => /^\d+ hours/.test(b.text()))
    expect(durationButtons).toHaveLength(3)
    expect(durationButtons.map(b => b.text())).toEqual(['24 hours', '48 hours', '72 hours (recommended)'])
  })

  it('defaults duration to 72h (active state)', () => {
    const wrapper = mountSettings()
    const btn72 = wrapper.findAll('button').find(b => b.text() === '72 hours (recommended)')
    expect(btn72.classes().join(' ')).toContain('text-white')
  })

  it('renders platform mode buttons', () => {
    const wrapper = mountSettings()
    const platformButtons = wrapper.findAll('button').filter(b =>
      ['Twitter', 'Reddit', 'Both'].includes(b.text())
    )
    expect(platformButtons).toHaveLength(3)
  })

  it('defaults platform mode to Both (parallel)', () => {
    const wrapper = mountSettings()
    const bothBtn = wrapper.findAll('button').find(b => b.text() === 'Both')
    expect(bothBtn.classes().join(' ')).toContain('text-white')
  })

  it('changes duration when button clicked', async () => {
    const wrapper = mountSettings()
    const btn24 = wrapper.findAll('button').find(b => b.text() === '24 hours')
    await btn24.trigger('click')
    expect(btn24.classes().join(' ')).toContain('text-white')
    const btn72 = wrapper.findAll('button').find(b => b.text() === '72 hours (recommended)')
    expect(btn72.classes().join(' ')).not.toContain('text-white')
  })

  it('changes platform mode when button clicked', async () => {
    const wrapper = mountSettings()
    const twitterBtn = wrapper.findAll('button').find(b => b.text() === 'Twitter')
    await twitterBtn.trigger('click')
    expect(twitterBtn.classes().join(' ')).toContain('text-white')
    const bothBtn = wrapper.findAll('button').find(b => b.text() === 'Both')
    expect(bothBtn.classes().join(' ')).not.toContain('text-white')
  })

  // ── Settings persistence ──────────────────────────────────────────

  it('saves simulation defaults to localStorage', async () => {
    const wrapper = mountSettings()
    const btn24 = wrapper.findAll('button').find(b => b.text() === '24 hours')
    await btn24.trigger('click')
    const stored = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(stored.duration).toBe(24)
    expect(stored.agentCount).toBe(200)
    expect(stored.platformMode).toBe('parallel')
  })

  it('loads saved simulation defaults from localStorage', async () => {
    localStorage.setItem('mirofish-settings', JSON.stringify({
      provider: 'openai',
      apiKey: 'sk-test',
      zepKey: 'zep-test',
      agentCount: 350,
      duration: 48,
      platformMode: 'reddit',
    }))
    const wrapper = mountSettings()
    await nextTick()
    const slider = wrapper.find('input[type="range"]')
    expect(slider.element.value).toBe('350')
    const btn48 = wrapper.findAll('button').find(b => b.text() === '48 hours')
    expect(btn48.classes().join(' ')).toContain('text-white')
    const redditBtn = wrapper.findAll('button').find(b => b.text() === 'Reddit')
    expect(redditBtn.classes().join(' ')).toContain('text-white')
  })

  it('selects correct LLM provider from saved settings', async () => {
    localStorage.setItem('mirofish-settings', JSON.stringify({ provider: 'gemini' }))
    const wrapper = mountSettings()
    await nextTick()
    const radios = wrapper.findAll('input[type="radio"]')
    const selected = radios.find(r => r.element.checked)
    expect(selected.element.value).toBe('gemini')
  })

  // ── Test Connection button states ─────────────────────────────────

  it('shows Testing... state when test connection is clicked', async () => {
    global.fetch = vi.fn().mockReturnValue(new Promise(() => {}))
    const wrapper = mountSettings()
    const apiKeyInput = wrapper.findAll('input[type="password"]')[0]
    await apiKeyInput.setValue('sk-test-key')
    const testButtons = wrapper.findAll('button').filter(b => b.text() === 'Test Connection')
    await testButtons[0].trigger('click')
    expect(wrapper.text()).toContain('Testing\u2026')
  })

  // ── Info section ──────────────────────────────────────────────────

  it('renders the info section about local storage', () => {
    const wrapper = mountSettings()
    expect(wrapper.text()).toContain('Settings are stored locally in your browser')
  })
})
