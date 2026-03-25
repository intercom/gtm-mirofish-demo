import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useSimulationStore } from '../stores/simulation'
import ScenarioBuilderView from '../views/ScenarioBuilderView.vue'
import SimulationWorkspaceView from '../views/SimulationWorkspaceView.vue'

// ── Router mock ──────────────────────────────────────────────
const mockPush = vi.fn()
const mockReplace = vi.fn()
let routeQuery = {}

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useRoute: () => ({ params: {}, query: routeQuery }),
}))

// ── Graph API mock ──────────────────────────────────────────
const mockGraphBuild = vi.fn()
const mockGetTask = vi.fn()
const mockGetData = vi.fn()

vi.mock('../api/graph', () => ({
  graphApi: {
    build: (...args) => mockGraphBuild(...args),
    getTask: (...args) => mockGetTask(...args),
    getData: (...args) => mockGetData(...args),
    getProject: vi.fn(),
    listProjects: vi.fn(),
    deleteProject: vi.fn(),
    resetProject: vi.fn(),
    generateOntology: vi.fn(),
    listTasks: vi.fn(),
    deleteGraph: vi.fn(),
  },
}))

// ── Axios client mock (used by useSimulationPolling) ────────
const mockClientGet = vi.fn()

vi.mock('../api/client', () => ({
  default: {
    get: (...args) => mockClientGet(...args),
    post: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE: '/api',
}))

// ── Toast mock ──────────────────────────────────────────────
vi.mock('../composables/useToast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  }),
}))

// ── Test fixture ────────────────────────────────────────────
const mockScenario = {
  id: 'outbound_campaign',
  name: 'Outbound Campaign Pre-Testing',
  description: 'Simulate outbound campaign effectiveness.',
  seed_text: 'Subject: Why teams are switching to Intercom...',
  agent_config: {
    count: 250,
    persona_types: ['VP of Support', 'CX Director', 'IT Leader', 'Technical Evaluator'],
    firmographic_mix: {
      industries: ['SaaS', 'Healthcare', 'Fintech'],
      company_sizes: ['50-200', '200-500'],
      regions: ['North America', 'EMEA'],
    },
  },
  simulation_config: {
    total_hours: 48,
    minutes_per_round: 30,
    platform_mode: 'parallel',
  },
}

describe('E2E: scenario creation and simulation launch', () => {
  let pinia

  beforeEach(() => {
    vi.clearAllMocks()
    routeQuery = {}
    pinia = createPinia()
    setActivePinia(pinia)

    localStorage.removeItem('mirofish_simulation_runs')

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockScenario),
    })

    mockGraphBuild.mockResolvedValue({
      data: { task_id: 'task-abc-123', project_id: 'proj-xyz-789' },
    })
  })

  afterEach(() => {
    delete global.fetch
  })

  function mountScenarioBuilder(id = 'outbound_campaign') {
    return mount(ScenarioBuilderView, {
      props: { id },
      global: {
        plugins: [pinia],
        stubs: { 'router-link': { template: '<a><slot /></a>' } },
      },
    })
  }

  // ── Phase 1: Scenario loading ─────────────────────────────

  it('loads scenario from API and pre-fills all form fields', async () => {
    const wrapper = mountScenarioBuilder()
    await flushPromises()

    expect(global.fetch).toHaveBeenCalledWith('/api/gtm/scenarios/outbound_campaign')
    expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')

    expect(wrapper.find('textarea').element.value).toContain(
      'Why teams are switching to Intercom',
    )
    expect(wrapper.find('input[type="range"]').element.value).toBe('250')

    const durationBtns = wrapper.findAll('button').filter(b => /^\d+h$/.test(b.text()))
    expect(durationBtns.find(b => b.text() === '48h').classes().join(' ')).toContain('text-white')

    const personaBtns = wrapper
      .findAll('button')
      .filter(b => mockScenario.agent_config.persona_types.includes(b.text()))
    expect(personaBtns).toHaveLength(4)
    personaBtns.forEach(btn => expect(btn.classes().join(' ')).toContain('text-white'))

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes).toHaveLength(3)
    checkboxes.forEach(cb => expect(cb.element.checked).toBe(true))
  })

  // ── Phase 2: Configuration modification ───────────────────

  it('allows editing configuration before launch', async () => {
    const wrapper = mountScenarioBuilder()
    await flushPromises()

    await wrapper.find('textarea').setValue('Custom enterprise campaign')
    expect(wrapper.find('textarea').element.value).toBe('Custom enterprise campaign')

    await wrapper.find('input[type="range"]').setValue(300)
    expect(wrapper.find('input[type="range"]').element.value).toBe('300')

    const vpBtn = wrapper.findAll('button').find(b => b.text() === 'VP of Support')
    await vpBtn.trigger('click')
    expect(vpBtn.classes().join(' ')).not.toContain('text-white')

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].setValue(false)
    expect(checkboxes[0].element.checked).toBe(false)
  })

  // ── Phase 3: Simulation launch ────────────────────────────

  it('launches simulation with correct API payload and updates store', async () => {
    const wrapper = mountScenarioBuilder()
    await flushPromises()

    const runBtn = wrapper.findAll('button').find(b => b.text() === 'Run Simulation')
    expect(runBtn.attributes('disabled')).toBeUndefined()

    await runBtn.trigger('click')
    await flushPromises()

    // Correct API payload
    expect(mockGraphBuild).toHaveBeenCalledOnce()
    expect(mockGraphBuild.mock.calls[0][0]).toEqual({
      seed_text: mockScenario.seed_text,
      agent_count: 250,
      persona_types: mockScenario.agent_config.persona_types,
      industries: mockScenario.agent_config.firmographic_mix.industries,
      company_sizes: [],
      regions: [],
      duration_hours: 48,
      minutes_per_round: 30,
      platform_mode: 'parallel',
    })

    // Store state
    const store = useSimulationStore()
    expect(store.status).toBe('building_graph')
    expect(store.graphTaskId).toBe('task-abc-123')
    expect(store.scenarioConfig).toMatchObject({
      scenarioId: 'outbound_campaign',
      scenarioName: 'Outbound Campaign Pre-Testing',
      agentCount: 250,
      duration: 48,
      platformMode: 'parallel',
    })
    expect(store.scenarioConfig.personas).toEqual(mockScenario.agent_config.persona_types)
    expect(store.scenarioConfig.industries).toEqual(
      mockScenario.agent_config.firmographic_mix.industries,
    )

    // Session run recorded
    expect(store.sessionRuns).toHaveLength(1)
    expect(store.sessionRuns[0]).toMatchObject({
      id: 'task-abc-123',
      scenarioId: 'outbound_campaign',
      status: 'building_graph',
    })

    // Navigation
    expect(mockPush).toHaveBeenCalledWith('/workspace/task-abc-123')
  })

  it('sends modified parameters when user changes config before launch', async () => {
    const wrapper = mountScenarioBuilder()
    await flushPromises()

    await wrapper.find('textarea').setValue('Modified campaign text')
    await wrapper.find('input[type="range"]').setValue(150)

    // Toggle VP of Support off
    const vpBtn = wrapper.findAll('button').find(b => b.text() === 'VP of Support')
    await vpBtn.trigger('click')

    // Uncheck first industry (SaaS)
    await wrapper.findAll('input[type="checkbox"]')[0].setValue(false)

    // Change duration to 72h
    const dur72 = wrapper.findAll('button').find(b => b.text() === '72h')
    await dur72.trigger('click')

    // Change platform to twitter
    const twitterBtn = wrapper.findAll('button').find(b => b.text() === 'twitter')
    await twitterBtn.trigger('click')

    const runBtn = wrapper.findAll('button').find(b => b.text() === 'Run Simulation')
    await runBtn.trigger('click')
    await flushPromises()

    const payload = mockGraphBuild.mock.calls[0][0]
    expect(payload.seed_text).toBe('Modified campaign text')
    expect(payload.agent_count).toBe(150)
    expect(payload.persona_types).toEqual(['CX Director', 'IT Leader', 'Technical Evaluator'])
    expect(payload.industries).toEqual(['Healthcare', 'Fintech'])
    expect(payload.duration_hours).toBe(72)
    expect(payload.platform_mode).toBe('twitter')
  })

  // ── Phase 4: Error handling ───────────────────────────────

  it('handles launch error gracefully without navigating', async () => {
    mockGraphBuild.mockRejectedValue({ message: 'LLM service unavailable' })

    const wrapper = mountScenarioBuilder()
    await flushPromises()

    const runBtn = wrapper.findAll('button').find(b => b.text() === 'Run Simulation')
    await runBtn.trigger('click')
    await flushPromises()

    expect(mockPush).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('LLM service unavailable')

    const store = useSimulationStore()
    expect(store.status).toBe('idle')
    expect(store.sessionRuns).toHaveLength(0)
  })

  // ── Phase 5: Workspace polling bootstrap ──────────────────

  describe('workspace polling after launch', () => {
    beforeEach(() => {
      vi.useFakeTimers()

      mockGetTask.mockResolvedValue({
        data: {
          success: true,
          data: { status: 'building', progress: 30, message: 'Generating ontology...' },
        },
      })

      mockClientGet.mockImplementation((url) => {
        if (url.includes('/run-status/detail')) {
          return Promise.resolve({
            data: { success: true, data: { recent_actions: [] } },
          })
        }
        if (url.includes('/run-status')) {
          return Promise.resolve({
            data: {
              success: true,
              data: {
                runner_status: 'idle',
                progress_percent: 0,
                current_round: 0,
                total_rounds: 0,
              },
            },
          })
        }
        if (url.includes('/timeline')) {
          return Promise.resolve({
            data: { success: true, data: { timeline: [] } },
          })
        }
        return Promise.resolve({ data: {} })
      })
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    function mountWorkspace(taskId = 'task-abc-123') {
      return mount(SimulationWorkspaceView, {
        props: { taskId },
        global: {
          plugins: [pinia],
          stubs: {
            'router-link': { template: '<a><slot /></a>' },
            WorkspacePhaseNav: { template: '<div data-testid="phase-nav"></div>' },
            GraphPanel: { template: '<div data-testid="graph-panel"></div>' },
            SimulationPanel: { template: '<div data-testid="sim-panel"></div>' },
          },
        },
      })
    }

    it('starts polling graph task and run status on mount', async () => {
      mountWorkspace()
      await flushPromises()

      expect(mockGetTask).toHaveBeenCalledWith('task-abc-123')
      const runStatusCalls = mockClientGet.mock.calls.filter(
        ([url]) => url.includes('/run-status') && !url.includes('/detail'),
      )
      expect(runStatusCalls.length).toBeGreaterThanOrEqual(1)
    })

    it('continues polling graph task at 2-second intervals', async () => {
      mountWorkspace()
      await flushPromises()

      const initialCalls = mockGetTask.mock.calls.length

      vi.advanceTimersByTime(2000)
      await flushPromises()

      expect(mockGetTask.mock.calls.length).toBeGreaterThan(initialCalls)
    })

    it('fetches graph data when graph build completes', async () => {
      mountWorkspace()
      await flushPromises()

      // Transition to completed on next poll
      mockGetTask.mockResolvedValue({
        data: {
          success: true,
          data: {
            status: 'completed',
            progress: 100,
            result: { graph_id: 'graph-001' },
          },
        },
      })

      mockGetData.mockResolvedValue({
        data: {
          success: true,
          data: { nodes: [{ id: '1', label: 'VP Support' }], edges: [], node_count: 1, edge_count: 0 },
        },
      })

      vi.advanceTimersByTime(2000)
      await flushPromises()

      expect(mockGetData).toHaveBeenCalledWith('graph-001')
    })

    it('stops graph polling after build completes', async () => {
      mountWorkspace()
      await flushPromises()

      mockGetTask.mockResolvedValue({
        data: {
          success: true,
          data: { status: 'completed', progress: 100, result: { graph_id: 'graph-001' } },
        },
      })
      mockGetData.mockResolvedValue({
        data: { success: true, data: { nodes: [], edges: [] } },
      })

      vi.advanceTimersByTime(2000)
      await flushPromises()

      const callsAfterComplete = mockGetTask.mock.calls.length

      vi.advanceTimersByTime(4000)
      await flushPromises()

      // No more graph task polls after completion
      expect(mockGetTask.mock.calls.length).toBe(callsAfterComplete)
    })

    it('falls back to demo mode on network error', async () => {
      mockGetTask.mockRejectedValue({ status: 0, message: 'Network error' })

      mountWorkspace()
      await flushPromises()

      // Workspace should still render without crashing
      expect(mockGetTask).toHaveBeenCalled()
    })
  })

  // ── Phase 6: Custom scenario template ─────────────────────

  it('custom scenario starts empty and populates from template', async () => {
    const wrapper = mountScenarioBuilder('custom')
    await flushPromises()

    expect(wrapper.text()).toContain('Custom Simulation')
    expect(wrapper.find('textarea').element.value).toBe('')
    expect(wrapper.text()).toContain('Start from a template')

    const templateBtn = wrapper
      .findAll('button')
      .find(b => b.text().includes('Competitive Displacement Campaign'))
    await templateBtn.trigger('click')
    await flushPromises()

    expect(wrapper.find('textarea').element.value).toContain(
      'Why leading support teams are switching from Zendesk',
    )
    expect(wrapper.find('input[type="range"]').element.value).toBe('250')
  })

  it('can launch simulation from custom scenario with applied template', async () => {
    const wrapper = mountScenarioBuilder('custom')
    await flushPromises()

    // Apply template first
    const templateBtn = wrapper
      .findAll('button')
      .find(b => b.text().includes('Product Launch Announcement'))
    await templateBtn.trigger('click')
    await flushPromises()

    // Select personas (template applies them)
    const runBtn = wrapper.findAll('button').find(b => b.text() === 'Run Simulation')
    expect(runBtn.attributes('disabled')).toBeUndefined()

    await runBtn.trigger('click')
    await flushPromises()

    expect(mockGraphBuild).toHaveBeenCalledOnce()
    const payload = mockGraphBuild.mock.calls[0][0]
    expect(payload.seed_text).toContain('Introducing Intercom Workflows 2.0')
    expect(payload.persona_types).toEqual([
      'Product Manager',
      'End User',
      'Champion',
      'Technical Evaluator',
    ])
    expect(payload.industries).toEqual(['SaaS', 'E-commerce', 'Fintech'])
    expect(payload.agent_count).toBe(200)

    expect(mockPush).toHaveBeenCalledWith('/workspace/task-abc-123')

    const store = useSimulationStore()
    expect(store.status).toBe('building_graph')
    expect(store.scenarioConfig.scenarioName).toBe('Custom Simulation')
  })
})
