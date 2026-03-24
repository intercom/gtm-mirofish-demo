import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ScenarioBuilderView from '../ScenarioBuilderView.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const mockScenario = {
  id: 'outbound_campaign',
  name: 'Outbound Campaign Pre-Testing',
  description: 'Simulate how AI-generated outbound emails land.',
  seed_text: 'Intercom is launching a campaign...',
  agent_config: {
    count: 200,
    persona_types: ['VP of Support', 'CX Director', 'IT Leader'],
    firmographic_mix: {
      industries: ['SaaS', 'Healthcare', 'Fintech'],
    },
  },
  simulation_config: {
    total_hours: 48,
    minutes_per_round: 30,
    platform_mode: 'twitter',
  },
}

function mountWithFetch(scenario = mockScenario) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(scenario),
  })

  return mount(ScenarioBuilderView, {
    props: { id: 'outbound_campaign' },
    global: {
      stubs: { 'router-link': { template: '<a><slot /></a>' } },
    },
  })
}

describe('ScenarioBuilderView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    global.fetch = vi.fn().mockReturnValue(new Promise(() => {}))
    const wrapper = mount(ScenarioBuilderView, {
      props: { id: 'test' },
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>' } },
      },
    })
    expect(wrapper.text()).toContain('Loading scenario...')
  })

  it('fetches scenario from API on mount', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    expect(global.fetch).toHaveBeenCalledWith('/api/gtm/scenarios/outbound_campaign')
  })

  it('displays scenario name and description', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
    expect(wrapper.text()).toContain('Simulate how AI-generated outbound emails land.')
  })

  it('pre-fills seed text from scenario data', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const textarea = wrapper.find('textarea')
    expect(textarea.element.value).toBe('Intercom is launching a campaign...')
  })

  it('pre-fills agent count from scenario config', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const slider = wrapper.find('input[type="range"]')
    expect(slider.element.value).toBe('200')
    expect(slider.attributes('min')).toBe('50')
    expect(slider.attributes('max')).toBe('500')
  })

  it('pre-selects duration from scenario config', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const durationButtons = wrapper.findAll('button').filter(b => /^\d+h$/.test(b.text()))
    const activeButton = durationButtons.find(b => b.text() === '48h')
    expect(activeButton.classes().join(' ')).toContain('text-white')
  })

  it('pre-selects platform mode from scenario config', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const platformButtons = wrapper.findAll('button').filter(b =>
      ['twitter', 'reddit', 'Both'].includes(b.text())
    )
    const activeButton = platformButtons.find(b => b.text() === 'twitter')
    expect(activeButton.classes().join(' ')).toContain('text-white')
  })

  it('renders all persona type buttons as selected', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const personaButtons = wrapper.findAll('button').filter(b =>
      mockScenario.agent_config.persona_types.includes(b.text())
    )
    expect(personaButtons).toHaveLength(3)
    personaButtons.forEach(btn => {
      expect(btn.classes().join(' ')).toContain('text-white')
    })
  })

  it('toggles persona off when clicked', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const vpButton = wrapper.findAll('button').find(b => b.text() === 'VP of Support')
    await vpButton.trigger('click')
    expect(vpButton.classes().join(' ')).not.toContain('text-white')
  })

  it('renders all industry checkboxes as checked', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(3)
    checkboxes.forEach(cb => {
      expect(cb.element.checked).toBe(true)
    })
  })

  it('toggles industry off when checkbox unchecked', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].setValue(false)
    expect(checkboxes[0].element.checked).toBe(false)
  })

  it('navigates on Run Simulation click', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const runButton = wrapper.findAll('button').find(b => b.text() === 'Run Simulation')
    await runButton.trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/graph/demo-task-id')
  })

  it('shows error state when scenario not found', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false })
    const wrapper = mount(ScenarioBuilderView, {
      props: { id: 'nonexistent' },
      global: {
        stubs: { 'router-link': { template: '<a><slot /></a>' } },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Scenario not found')
  })

  it('allows editing the seed text', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const textarea = wrapper.find('textarea')
    await textarea.setValue('New seed text content')
    expect(textarea.element.value).toBe('New seed text content')
  })

  it('allows adjusting agent count via slider', async () => {
    const wrapper = mountWithFetch()
    await flushPromises()
    const slider = wrapper.find('input[type="range"]')
    await slider.setValue(350)
    expect(slider.element.value).toBe('350')
  })
})
