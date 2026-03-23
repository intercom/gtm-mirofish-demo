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
  description: 'Test messaging before sending to real prospects.',
  seed_text: 'Intercom is launching an automated outbound campaign.',
  agent_config: {
    count: 200,
    persona_types: ['VP of Support', 'CX Director', 'IT Leader', 'Head of Operations'],
    firmographic_mix: {
      industries: ['SaaS', 'Healthcare', 'Fintech', 'E-commerce'],
    },
  },
  simulation_config: {
    total_hours: 72,
    minutes_per_round: 30,
    platform_mode: 'parallel',
  },
}

function createFetchMock(data, ok = true) {
  return vi.fn(() =>
    Promise.resolve({ ok, json: () => Promise.resolve(data) }),
  )
}

function mountView(props = { id: 'outbound_campaign' }) {
  return mount(ScenarioBuilderView, { props, shallow: false })
}

describe('ScenarioBuilderView', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    mockPush.mockClear()
  })

  it('shows loading state initially', () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    expect(wrapper.text()).toContain('Loading scenario...')
  })

  it('fetches scenario and pre-fills all form fields', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    expect(global.fetch).toHaveBeenCalledWith('/api/gtm/scenarios/outbound_campaign')
    expect(wrapper.find('h1').text()).toBe('Outbound Campaign Pre-Testing')
    expect(wrapper.find('textarea').element.value).toBe(mockScenario.seed_text)
  })

  it('renders agent count slider with min=50 max=500', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const slider = wrapper.find('input[type="range"]')
    expect(slider.attributes('min')).toBe('50')
    expect(slider.attributes('max')).toBe('500')
  })

  it('pre-fills agent count from scenario data', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('200')
  })

  it('renders all persona types as toggleable buttons', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const personaButtons = wrapper.findAll('button').filter((b) => {
      const text = b.text()
      return mockScenario.agent_config.persona_types.some((p) => text === p)
    })
    expect(personaButtons).toHaveLength(4)
  })

  it('pre-selects all persona types from scenario', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const personaButtons = wrapper.findAll('button').filter((b) =>
      mockScenario.agent_config.persona_types.includes(b.text()),
    )
    for (const btn of personaButtons) {
      expect(btn.classes()).toContain('bg-[#2068FF]')
    }
  })

  it('toggles persona type off on click', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const vpButton = wrapper.findAll('button').find((b) => b.text() === 'VP of Support')
    await vpButton.trigger('click')

    expect(vpButton.classes()).not.toContain('bg-[#2068FF]')
    expect(vpButton.classes()).toContain('bg-white')
  })

  it('renders all industry checkboxes', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(4)
    expect(wrapper.text()).toContain('SaaS')
    expect(wrapper.text()).toContain('Healthcare')
    expect(wrapper.text()).toContain('Fintech')
    expect(wrapper.text()).toContain('E-commerce')
  })

  it('pre-checks all industry checkboxes from scenario', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    for (const cb of checkboxes) {
      expect(cb.element.checked).toBe(true)
    }
  })

  it('toggles industry checkbox off on click', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].trigger('change')

    // After toggle, the SaaS checkbox should be unchecked
    expect(checkboxes[0].element.checked).toBe(false)
  })

  it('pre-fills duration from scenario config', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const select = wrapper.find('select')
    expect(select.element.value).toBe('72')
  })

  it('renders platform mode toggle with Both active by default for parallel', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const bothButton = wrapper.findAll('button').find((b) => b.text() === 'Both')
    expect(bothButton.classes()).toContain('bg-[#2068FF]')
  })

  it('switches platform mode on click', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const twitterBtn = wrapper.findAll('button').find((b) => b.text() === 'twitter')
    await twitterBtn.trigger('click')

    expect(twitterBtn.classes()).toContain('bg-[#2068FF]')
    const bothBtn = wrapper.findAll('button').find((b) => b.text() === 'Both')
    expect(bothBtn.classes()).not.toContain('bg-[#2068FF]')
  })

  it('has a Run Simulation button', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const runBtn = wrapper.findAll('button').find((b) => b.text() === 'Run Simulation')
    expect(runBtn).toBeTruthy()
  })

  it('navigates on Run Simulation click', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const runBtn = wrapper.findAll('button').find((b) => b.text() === 'Run Simulation')
    await runBtn.trigger('click')

    expect(mockPush).toHaveBeenCalledWith('/graph/demo-task-id')
  })

  it('shows error state when scenario not found', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false }))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('Scenario not found')
    expect(wrapper.text()).toContain('Back to Home')
  })

  it('allows editing the seed text', async () => {
    global.fetch = createFetchMock(mockScenario)
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('Custom seed text')
    expect(textarea.element.value).toBe('Custom seed text')
  })

  it('clamps agent count to min 50 if scenario value is lower', async () => {
    const scenario = {
      ...mockScenario,
      agent_config: { ...mockScenario.agent_config, count: 10 },
    }
    global.fetch = createFetchMock(scenario)
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('50')
  })
})
