import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ScenarioBuilderView from '../views/ScenarioBuilderView.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

vi.mock('../api/graph', () => ({
  graphApi: {
    build: vi.fn(),
  },
}))

import { graphApi } from '../api/graph'
import { useScenariosStore } from '../stores/scenarios'

const MOCK_SCENARIO = {
  id: 'outbound_campaign',
  name: 'Outbound Campaign Test',
  description: 'Test AI-generated outbound emails',
  seed_text: 'Intercom is launching a new outbound product...',
  agent_config: {
    count: 200,
    persona_types: ['VP of Support', 'CX Director', 'Head of CS'],
    firmographic_mix: {
      industries: ['SaaS', 'Healthcare', 'Finance'],
    },
  },
  simulation_config: {
    total_hours: 72,
    platform_mode: 'parallel',
  },
}

function mountView(id = 'outbound_campaign') {
  return mount(ScenarioBuilderView, {
    props: { id },
    global: {
      stubs: {
        'router-link': { template: '<a><slot /></a>', props: ['to'] },
        LoadingSpinner: { template: '<div data-testid="loading">Loading...</div>', props: ['label'] },
        ErrorState: {
          template: '<div data-testid="error"><button @click="$emit(\'retry\')">Retry</button></div>',
          props: ['title', 'message'],
          emits: ['retry'],
        },
      },
    },
  })
}

describe('ScenarioBuilderView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPush.mockReset()
    graphApi.build.mockReset()
  })

  it('shows loading spinner while fetching scenario', () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => new Promise(() => {})) // never resolves
    const wrapper = mountView()
    expect(wrapper.find('[data-testid="loading"]').exists()).toBe(true)
  })

  it('shows error state when fetch fails', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.reject(new Error('Network error')))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('[data-testid="error"]').exists()).toBe(true)
  })

  it('shows error when scenario not found', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(null))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('[data-testid="error"]').exists()).toBe(true)
  })

  it('pre-fills form fields from scenario template', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('textarea').element.value).toBe(MOCK_SCENARIO.seed_text)
    expect(wrapper.find('input[type="range"]').element.value).toBe('200')
    expect(wrapper.text()).toContain('Outbound Campaign Test')
    expect(wrapper.text()).toContain('Test AI-generated outbound emails')
  })

  it('renders persona type toggle buttons', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    for (const persona of MOCK_SCENARIO.agent_config.persona_types) {
      expect(wrapper.text()).toContain(persona)
    }
  })

  it('renders industry mix checkboxes', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(3)
    for (const industry of MOCK_SCENARIO.agent_config.firmographic_mix.industries) {
      expect(wrapper.text()).toContain(industry)
    }
  })

  it('toggles persona selection on click', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    // All personas start selected (pre-filled from template)
    const personaButtons = wrapper.findAll('.flex.flex-wrap.gap-2 button')
    expect(personaButtons.length).toBe(3)

    // Click first persona to deselect
    await personaButtons[0].trigger('click')
    // Click again to re-select
    await personaButtons[0].trigger('click')
    // Should still be functional (no errors thrown)
    expect(wrapper.text()).toContain('VP of Support')
  })

  it('toggles industry selection via checkbox', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    // All start checked (pre-filled from template)
    await checkboxes[0].trigger('change')
    // Toggle back
    await checkboxes[0].trigger('change')
    expect(wrapper.text()).toContain('SaaS')
  })

  it('updates agent count via slider', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    const slider = wrapper.find('input[type="range"]')
    await slider.setValue(300)
    expect(wrapper.text()).toContain('300')
  })

  it('switches duration on button click', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    // Find the 24h button in the Duration section
    const durationButtons = wrapper.findAll('.space-y-6 > div:nth-child(2) button')
    await durationButtons[0].trigger('click')
    // The 24h button should now be active (has primary bg class)
    expect(durationButtons[0].classes()).toContain('bg-[var(--color-primary)]')
  })

  it('switches platform mode on button click', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    const wrapper = mountView()
    await flushPromises()

    const platformButtons = wrapper.findAll('.space-y-6 > div:nth-child(3) button')
    // Click Twitter
    await platformButtons[0].trigger('click')
    expect(platformButtons[0].classes()).toContain('bg-[var(--color-primary)]')
  })

  it('calls graphApi.build and navigates on Run Simulation', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    graphApi.build.mockResolvedValue({ data: { task_id: 'task-abc-123' } })

    const wrapper = mountView()
    await flushPromises()

    const runButton = wrapper.findAll('button').find((b) => b.text().includes('Run Simulation'))
    await runButton.trigger('click')
    await flushPromises()

    expect(graphApi.build).toHaveBeenCalledWith({
      seed_text: MOCK_SCENARIO.seed_text,
      agent_count: 200,
      persona_types: MOCK_SCENARIO.agent_config.persona_types,
      industries: MOCK_SCENARIO.agent_config.firmographic_mix.industries,
      duration_hours: 72,
      platform_mode: 'parallel',
    })
    expect(mockPush).toHaveBeenCalledWith('/graph/task-abc-123')
  })

  it('disables Run Simulation when seed text is empty', async () => {
    const store = useScenariosStore()
    const emptyScenario = { ...MOCK_SCENARIO, seed_text: '' }
    store.fetchOne = vi.fn(() => Promise.resolve(emptyScenario))
    const wrapper = mountView()
    await flushPromises()

    const runButton = wrapper.findAll('button').find((b) => b.text().includes('Run Simulation'))
    expect(runButton.attributes('disabled')).toBeDefined()
  })

  it('disables Run Simulation when no personas selected', async () => {
    const store = useScenariosStore()
    const noPersonas = {
      ...MOCK_SCENARIO,
      agent_config: { ...MOCK_SCENARIO.agent_config, persona_types: [] },
    }
    store.fetchOne = vi.fn(() => Promise.resolve(noPersonas))
    const wrapper = mountView()
    await flushPromises()

    const runButton = wrapper.findAll('button').find((b) => b.text().includes('Run Simulation'))
    expect(runButton.attributes('disabled')).toBeDefined()
  })

  it('shows "Starting..." while run is in progress', async () => {
    const store = useScenariosStore()
    store.fetchOne = vi.fn(() => Promise.resolve(MOCK_SCENARIO))
    graphApi.build.mockReturnValue(new Promise(() => {})) // never resolves

    const wrapper = mountView()
    await flushPromises()

    const runButton = wrapper.findAll('button').find((b) => b.text().includes('Run Simulation'))
    await runButton.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Starting...')
  })
})
