import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SettingsView from '../SettingsView.vue'

const stubs = {
  'router-link': { template: '<a><slot /></a>' },
}

// Helper: build a fetch mock that routes by URL
function createFetchRouter(routes = {}) {
  return vi.fn((url, opts) => {
    for (const [pattern, handler] of Object.entries(routes)) {
      if (url.includes(pattern)) {
        const result = typeof handler === 'function' ? handler(url, opts) : handler
        return Promise.resolve({
          ok: result.ok ?? true,
          json: () => Promise.resolve(result.body ?? result),
        })
      }
    }
    // Default: auth-status returns disabled
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ authEnabled: false, user: null, provider: null }),
    })
  })
}

function mountSettings() {
  return mount(SettingsView, { global: { stubs } })
}

describe('Settings E2E: full configuration journeys', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ authEnabled: false, user: null, provider: null }),
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  // ── Journey: complete settings configuration ──────────────────────

  it('configures provider, API keys, and simulation defaults in a single session', async () => {
    const wrapper = mountSettings()
    await flushPromises()

    // Step 1: Switch to OpenAI provider
    const radios = wrapper.findAll('input[type="radio"]')
    await radios[1].setValue(true) // openai
    await wrapper.vm.$nextTick()

    // Verify provider switched
    expect(wrapper.find('input[type="radio"][value="openai"]').element.checked).toBe(true)
    expect(wrapper.text()).toContain('gpt-4o')

    // Step 2: Enter LLM API key
    const passwordInputs = wrapper.findAll('input[type="password"]')
    await passwordInputs[0].setValue('sk-test-openai-key')
    await wrapper.vm.$nextTick()

    // Step 3: Enter Zep API key
    await passwordInputs[1].setValue('zep-cloud-key-123')
    await wrapper.vm.$nextTick()

    // Step 4: Adjust agent count slider
    const slider = wrapper.find('input[type="range"]')
    await slider.setValue(350)
    await wrapper.vm.$nextTick()

    // Step 5: Change platform mode to Twitter
    const twitterBtn = wrapper.findAll('button').find((b) => b.text() === 'Twitter')
    await twitterBtn.trigger('click')
    await wrapper.vm.$nextTick()

    // Step 6: Change duration to 24 hours
    const dur24Btn = wrapper.findAll('button').find((b) => b.text() === '24 hours')
    await dur24Btn.trigger('click')
    await wrapper.vm.$nextTick()

    // Verify everything persisted to localStorage
    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved).toMatchObject({
      provider: 'openai',
      apiKey: 'sk-test-openai-key',
      zepKey: 'zep-cloud-key-123',
      agentCount: 350,
      platformMode: 'twitter',
      duration: 24,
    })
  })

  // ── Journey: settings persist across page reload ──────────────────

  it('restores all settings after unmount and remount', async () => {
    // Session 1: configure everything
    const wrapper1 = mountSettings()
    await flushPromises()

    await wrapper1.findAll('input[type="radio"]')[2].setValue(true) // gemini
    await wrapper1.findAll('input[type="password"]')[0].setValue('gemini-key')
    await wrapper1.findAll('input[type="password"]')[1].setValue('zep-key')
    await wrapper1.find('input[type="range"]').setValue(100)
    const redditBtn = wrapper1.findAll('button').find((b) => b.text() === 'Reddit')
    await redditBtn.trigger('click')
    const dur48Btn = wrapper1.findAll('button').find((b) => b.text() === '48 hours')
    await dur48Btn.trigger('click')
    await wrapper1.vm.$nextTick()
    wrapper1.unmount()

    // Session 2: remount and verify all settings restored
    const wrapper2 = mountSettings()
    await flushPromises()

    expect(wrapper2.find('input[type="radio"][value="gemini"]').element.checked).toBe(true)
    expect(wrapper2.findAll('input[type="password"]')[0].element.value).toBe('gemini-key')
    expect(wrapper2.findAll('input[type="password"]')[1].element.value).toBe('zep-key')
    expect(wrapper2.find('input[type="range"]').element.value).toBe('100')
  })

  // ── Journey: LLM connection test lifecycle ────────────────────────

  it('tests LLM connection: enter key → test → success', async () => {
    const fetchMock = createFetchRouter({
      'test-llm': { ok: true, body: { ok: true } },
    })
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchMock)

    const wrapper = mountSettings()
    await flushPromises()

    // Enter API key to enable the test button
    await wrapper.findAll('input[type="password"]')[0].setValue('sk-valid-key')
    await wrapper.vm.$nextTick()

    // Find and click the LLM Test Connection button
    const testBtns = wrapper.findAll('button').filter((b) => b.text().includes('Test Connection'))
    expect(testBtns[0].attributes('disabled')).toBeUndefined()
    await testBtns[0].trigger('click')
    await flushPromises()

    // Verify success state
    expect(wrapper.text()).toContain('Connected')

    // Verify correct endpoint was called with provider and key
    const llmCall = fetchMock.mock.calls.find(([url]) => url.includes('test-llm'))
    expect(llmCall).toBeTruthy()
    const body = JSON.parse(llmCall[1].body)
    expect(body.provider).toBe('anthropic')
    expect(body.apiKey).toBe('sk-valid-key')
  })

  it('tests LLM connection: enter key → test → failure with error message', async () => {
    const fetchMock = createFetchRouter({
      'test-llm': { ok: false, body: { ok: false, error: 'Invalid API key format' } },
    })
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchMock)

    const wrapper = mountSettings()
    await flushPromises()

    await wrapper.findAll('input[type="password"]')[0].setValue('bad-key')
    await wrapper.vm.$nextTick()

    const testBtn = wrapper.findAll('button').find((b) => b.text().includes('Test Connection'))
    await testBtn.trigger('click')
    await flushPromises()

    // Verify failure state and error message
    expect(wrapper.text()).toContain('Failed')
    expect(wrapper.text()).toContain('Invalid API key format')
  })

  // ── Journey: Zep connection test lifecycle ────────────────────────

  it('tests Zep connection: enter key → test → success', async () => {
    const fetchMock = createFetchRouter({
      'test-zep': { ok: true, body: { ok: true } },
    })
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchMock)

    const wrapper = mountSettings()
    await flushPromises()

    // Enter Zep key
    await wrapper.findAll('input[type="password"]')[1].setValue('zep-valid-key')
    await wrapper.vm.$nextTick()

    // Click the second Test Connection button (Zep)
    const testBtns = wrapper.findAll('button').filter((b) => b.text().includes('Test Connection'))
    await testBtns[1].trigger('click')
    await flushPromises()

    // Verify correct endpoint
    const zepCall = fetchMock.mock.calls.find(([url]) => url.includes('test-zep'))
    expect(zepCall).toBeTruthy()
    const body = JSON.parse(zepCall[1].body)
    expect(body.apiKey).toBe('zep-valid-key')
  })

  it('tests Zep connection: network error shows fallback message', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      if (url.includes('test-zep')) return Promise.reject(new Error('fetch failed'))
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ authEnabled: false }),
      })
    })

    const wrapper = mountSettings()
    await flushPromises()

    await wrapper.findAll('input[type="password"]')[1].setValue('some-key')
    await wrapper.vm.$nextTick()

    const testBtns = wrapper.findAll('button').filter((b) => b.text().includes('Test Connection'))
    await testBtns[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Network error')
  })

  // ── Journey: provider switch sends correct provider in connection test ──

  it('sends updated provider when testing connection after switching providers', async () => {
    const fetchMock = createFetchRouter({
      'test-llm': { ok: true, body: { ok: true } },
    })
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchMock)

    const wrapper = mountSettings()
    await flushPromises()

    // Switch to Gemini
    await wrapper.findAll('input[type="radio"]')[2].setValue(true)
    await wrapper.vm.$nextTick()

    // Enter key and test
    await wrapper.findAll('input[type="password"]')[0].setValue('gemini-key')
    await wrapper.vm.$nextTick()

    const testBtn = wrapper.findAll('button').find((b) => b.text().includes('Test Connection'))
    await testBtn.trigger('click')
    await flushPromises()

    const llmCall = fetchMock.mock.calls.find(([url]) => url.includes('test-llm'))
    const body = JSON.parse(llmCall[1].body)
    expect(body.provider).toBe('gemini')
    expect(body.apiKey).toBe('gemini-key')
  })

  // ── Journey: simulation defaults configuration ────────────────────

  it('configures all simulation defaults and verifies active states', async () => {
    const wrapper = mountSettings()
    await flushPromises()

    // Change agent count
    await wrapper.find('input[type="range"]').setValue(450)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('450')

    // Switch to Reddit platform
    const redditBtn = wrapper.findAll('button').find((b) => b.text() === 'Reddit')
    await redditBtn.trigger('click')
    await wrapper.vm.$nextTick()

    // Verify Reddit button has active styling (bg- class from primary color)
    expect(redditBtn.classes().join(' ')).toContain('bg-')

    // Both button should no longer have active styling
    const bothBtn = wrapper.findAll('button').find((b) => b.text() === 'Both')
    expect(bothBtn.classes().join(' ')).not.toContain('text-white')

    // Switch duration to 48 hours
    const dur48 = wrapper.findAll('button').find((b) => b.text() === '48 hours')
    await dur48.trigger('click')
    await wrapper.vm.$nextTick()
    expect(dur48.classes().join(' ')).toContain('text-white')

    // Verify saved to localStorage
    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved.agentCount).toBe(450)
    expect(saved.platformMode).toBe('reddit')
    expect(saved.duration).toBe(48)
  })

  // ── Journey: info section renders context-appropriate guidance ──────

  it('shows localStorage guidance in non-demo mode', async () => {
    const wrapper = mountSettings()
    await flushPromises()

    expect(wrapper.text()).toContain('Settings are stored locally in your browser')
    expect(wrapper.text()).toContain('.env')
  })

  // ── Journey: theme switching ──────────────────────────────────────

  it('switches theme and persists preference', async () => {
    const wrapper = mountSettings()
    await flushPromises()

    // Click the Dark theme button
    const darkBtn = wrapper.findAll('button').find((b) => b.text().includes('Dark'))
    await darkBtn.trigger('click')
    await wrapper.vm.$nextTick()

    // Verify theme preference persisted to localStorage
    expect(localStorage.getItem('mirofish-theme')).toBe('dark')

    // Click Light theme button
    const lightBtn = wrapper.findAll('button').find((b) => b.text().includes('Light'))
    await lightBtn.trigger('click')
    await wrapper.vm.$nextTick()

    expect(localStorage.getItem('mirofish-theme')).toBe('light')
  })

  // ── Journey: disabled states when no API keys ─────────────────────

  it('disables both test buttons when keys are empty, enables when keys entered', async () => {
    const wrapper = mountSettings()
    await flushPromises()

    // Both test buttons should be disabled initially
    const testBtns = wrapper.findAll('button').filter((b) => b.text().includes('Test Connection'))
    expect(testBtns).toHaveLength(2)
    expect(testBtns[0].attributes('disabled')).toBeDefined()
    expect(testBtns[1].attributes('disabled')).toBeDefined()

    // Enter LLM key — first button should enable
    await wrapper.findAll('input[type="password"]')[0].setValue('key-1')
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('button').filter((b) => b.text().includes('Test Connection'))[0].attributes('disabled')).toBeUndefined()

    // Enter Zep key — second button should enable
    await wrapper.findAll('input[type="password"]')[1].setValue('key-2')
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('button').filter((b) => b.text().includes('Test Connection'))[1].attributes('disabled')).toBeUndefined()
  })

  // ── Journey: saved indicator appears on change ────────────────────

  it('shows saved indicator after making a change', async () => {
    vi.useFakeTimers()

    const wrapper = mountSettings()
    await flushPromises()

    // Initially no saved indicator
    expect(wrapper.text()).not.toContain('Saved')

    // Make a change
    await wrapper.findAll('input[type="radio"]')[1].setValue(true)
    await wrapper.vm.$nextTick()

    // Saved indicator should appear
    expect(wrapper.text()).toContain('Saved')

    // After 2 seconds it should disappear
    vi.advanceTimersByTime(2100)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).not.toContain('Saved')

    vi.useRealTimers()
  })

  // ── Journey: loading corrupted localStorage gracefully ────────────

  it('handles corrupted localStorage and falls back to defaults', async () => {
    localStorage.setItem('mirofish-settings', '{invalid json!!')

    const wrapper = mountSettings()
    await flushPromises()

    // Should fall back to defaults without crashing
    expect(wrapper.find('input[type="radio"][value="anthropic"]').element.checked).toBe(true)
    expect(wrapper.find('input[type="range"]').element.value).toBe('200')
  })

  // ── Journey: sequential provider switches with key persistence ────

  it('retains API key when switching between providers', async () => {
    const wrapper = mountSettings()
    await flushPromises()

    // Enter a key while on anthropic
    await wrapper.findAll('input[type="password"]')[0].setValue('my-secret-key')
    await wrapper.vm.$nextTick()

    // Switch to openai
    await wrapper.findAll('input[type="radio"]')[1].setValue(true)
    await wrapper.vm.$nextTick()

    // Key should still be present (same input field)
    expect(wrapper.findAll('input[type="password"]')[0].element.value).toBe('my-secret-key')

    // Switch to gemini
    await wrapper.findAll('input[type="radio"]')[2].setValue(true)
    await wrapper.vm.$nextTick()

    // Key still present
    expect(wrapper.findAll('input[type="password"]')[0].element.value).toBe('my-secret-key')

    // Verify localStorage tracks the final provider
    const saved = JSON.parse(localStorage.getItem('mirofish-settings'))
    expect(saved.provider).toBe('gemini')
    expect(saved.apiKey).toBe('my-secret-key')
  })
})
