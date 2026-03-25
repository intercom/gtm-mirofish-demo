import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

const mockPush = vi.fn()
const mockReplace = vi.fn()
let mockRoute = { params: {}, query: {} }

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useRoute: () => mockRoute,
}))

vi.mock('../../composables/useSimulationPolling', async () => {
  const vue = await import('vue')
  return {
    useSimulationPolling: vi.fn(() => ({
      graphTask: vue.ref(null),
      graphStatus: vue.ref('building'),
      graphProgress: vue.ref(0),
      graphData: vue.ref({ nodes: [], edges: [] }),
      graphId: vue.ref(null),
      runStatus: vue.ref(null),
      simStatus: vue.ref('idle'),
      recentActions: vue.ref([]),
      timeline: vue.ref([]),
      overallPhase: vue.computed(() => 'building_graph'),
      errorMsg: vue.ref(''),
      isDemoFallback: vue.ref(false),
      start: vi.fn(),
      stop: vi.fn(),
      setGraphData: vi.fn(),
      completeDemoRun: vi.fn(),
      forceRefresh: vi.fn(),
    })),
  }
})

import LandingView from '../LandingView.vue'
import SimulationsView from '../SimulationsView.vue'
import ScenarioBuilderView from '../ScenarioBuilderView.vue'
import ReportView from '../ReportView.vue'
import SimulationWorkspaceView from '../SimulationWorkspaceView.vue'
import { useSimulationStore } from '../../stores/simulation'
import { useSimulationPolling } from '../../composables/useSimulationPolling'

const RouterLinkStub = { template: '<a><slot /></a>', props: ['to'] }

function okJson(data) {
  return { ok: true, json: async () => data }
}

describe('Data views load correctly', () => {
  let originalFetch

  beforeEach(() => {
    originalFetch = global.fetch
    setActivePinia(createPinia())
    mockRoute = { params: {}, query: {} }
    vi.clearAllMocks()
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  // ---------------------------------------------------------------------------
  // LandingView — loads scenarios from /api/gtm/scenarios
  // ---------------------------------------------------------------------------
  describe('LandingView', () => {
    const landingStubs = {
      'router-link': RouterLinkStub,
      HeroSwarm: { template: '<div class="hero-swarm-stub" />' },
    }

    it('fetches scenarios from API and renders cards', async () => {
      global.fetch = vi.fn().mockResolvedValue(okJson({
        scenarios: [
          { id: 'sc1', name: 'Campaign Test', description: 'Test campaigns', icon: 'mail' },
          { id: 'sc2', name: 'Signal Check', description: 'Validate signals', icon: 'signal' },
        ],
      }))

      const wrapper = mount(LandingView, { global: { stubs: landingStubs } })
      await flushPromises()

      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/gtm/scenarios'))
      expect(wrapper.text()).toContain('Campaign Test')
      expect(wrapper.text()).toContain('Signal Check')
    })

    it('shows loading skeletons before data arrives', () => {
      global.fetch = vi.fn(() => new Promise(() => {}))
      const wrapper = mount(LandingView, { global: { stubs: landingStubs } })

      expect(wrapper.findAll('.animate-pulse').length).toBeGreaterThan(0)
    })

    it('falls back to hardcoded scenarios on fetch error', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
      const wrapper = mount(LandingView, { global: { stubs: landingStubs } })
      await flushPromises()

      const text = wrapper.text()
      expect(text).toContain('Outbound Campaign Pre-Testing')
      expect(text).toContain('Sales Signal Validation')
      expect(text).toContain('Pricing Change Simulation')
      expect(text).toContain('Personalization Optimization')
    })
  })

  // ---------------------------------------------------------------------------
  // SimulationsView — loads session runs from Pinia store (localStorage)
  // ---------------------------------------------------------------------------
  describe('SimulationsView', () => {
    function mountSimulations() {
      return mount(SimulationsView, {
        global: {
          stubs: {
            'router-link': RouterLinkStub,
            ConfirmDialog: { template: '<div />', props: ['modelValue', 'title', 'message', 'confirmLabel', 'destructive'] },
          },
        },
      })
    }

    it('shows empty state when store has no runs', () => {
      const wrapper = mountSimulations()

      expect(wrapper.text()).toContain('No simulation runs yet')
      expect(wrapper.text()).toContain('Run your first simulation')
    })

    it('renders run cards when store has session data', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        {
          id: 'run-1',
          scenarioId: 'outbound',
          scenarioName: 'Outbound Campaign',
          seedText: 'Test seed',
          agentCount: 200,
          personas: ['VP of Support'],
          industries: ['SaaS'],
          duration: 48,
          platformMode: 'parallel',
          totalRounds: 96,
          totalActions: 1250,
          twitterActions: 700,
          redditActions: 550,
          status: 'completed',
          timestamp: Date.now() - 3600000,
        },
        {
          id: 'run-2',
          scenarioId: 'pricing',
          scenarioName: 'Pricing Simulation',
          seedText: 'Price test',
          agentCount: 150,
          personas: ['CFO'],
          industries: ['Fintech'],
          duration: 72,
          platformMode: 'twitter',
          totalRounds: 48,
          totalActions: 600,
          twitterActions: 600,
          redditActions: 0,
          status: 'running',
          timestamp: Date.now() - 1800000,
        },
      ]

      const wrapper = mountSimulations()
      await flushPromises()

      expect(wrapper.text()).toContain('Outbound Campaign')
      expect(wrapper.text()).toContain('Pricing Simulation')
      expect(wrapper.text()).toContain('Completed')
      expect(wrapper.text()).toContain('In Progress')
    })

    it('displays summary statistics from store data', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        {
          id: 'run-a',
          scenarioName: 'Outbound Campaign',
          totalRounds: 96,
          totalActions: 800,
          twitterActions: 500,
          redditActions: 300,
          status: 'completed',
          timestamp: Date.now(),
        },
        {
          id: 'run-b',
          scenarioName: 'Outbound Campaign',
          totalRounds: 48,
          totalActions: 450,
          twitterActions: 250,
          redditActions: 200,
          status: 'completed',
          timestamp: Date.now(),
        },
      ]

      const wrapper = mountSimulations()
      await flushPromises()

      expect(wrapper.text()).toContain('Total Runs')
      expect(wrapper.text()).toContain('2')
      expect(wrapper.text()).toContain('Total Actions')
      expect(wrapper.text()).toContain('1,250')
      expect(wrapper.text()).toContain('Top Scenario')
      expect(wrapper.text()).toContain('Outbound Campaign')
    })

    it('displays per-card stats (rounds, actions, platform breakdown)', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        {
          id: 'run-x',
          scenarioName: 'Test Scenario',
          totalRounds: 72,
          totalActions: 900,
          twitterActions: 520,
          redditActions: 380,
          status: 'completed',
          timestamp: Date.now(),
        },
      ]

      const wrapper = mountSimulations()
      await flushPromises()

      expect(wrapper.text()).toContain('72')
      expect(wrapper.text()).toContain('900')
      expect(wrapper.text()).toContain('520')
      expect(wrapper.text()).toContain('380')
    })

    it('shows count badge in header when runs exist', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        { id: 'r1', scenarioName: 'S1', totalRounds: 1, totalActions: 1, twitterActions: 0, redditActions: 0, status: 'completed', timestamp: Date.now() },
        { id: 'r2', scenarioName: 'S2', totalRounds: 1, totalActions: 1, twitterActions: 0, redditActions: 0, status: 'completed', timestamp: Date.now() },
        { id: 'r3', scenarioName: 'S3', totalRounds: 1, totalActions: 1, twitterActions: 0, redditActions: 0, status: 'completed', timestamp: Date.now() },
      ]

      const wrapper = mountSimulations()
      await flushPromises()

      const badge = wrapper.find('.text-\\[\\#2068FF\\].bg-\\[rgba\\(32\\,104\\,255\\,0\\.08\\)\\]')
      expect(badge.exists()).toBe(true)
      expect(badge.text()).toBe('3')
    })

    it('filters runs by search query', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        { id: 'r1', scenarioName: 'Outbound Campaign', totalRounds: 10, totalActions: 100, twitterActions: 50, redditActions: 50, status: 'completed', timestamp: Date.now() },
        { id: 'r2', scenarioName: 'Pricing Simulation', totalRounds: 20, totalActions: 200, twitterActions: 100, redditActions: 100, status: 'completed', timestamp: Date.now() },
      ]

      const wrapper = mountSimulations()
      await flushPromises()

      expect(wrapper.findAll('[class*="border-[var(--color-border)]"][class*="rounded-lg"][class*="p-5"]').length).toBe(2)

      const input = wrapper.find('input[type="text"]')
      await input.setValue('Pricing')
      await flushPromises()

      const cards = wrapper.findAll('[class*="border-[var(--color-border)]"][class*="rounded-lg"][class*="p-5"]')
      expect(cards.length).toBe(1)
      expect(cards[0].text()).toContain('Pricing Simulation')
    })

    it('shows "no results" message when filter matches nothing', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        { id: 'r1', scenarioName: 'Outbound', totalRounds: 10, totalActions: 100, twitterActions: 50, redditActions: 50, status: 'completed', timestamp: Date.now() },
      ]

      const wrapper = mountSimulations()
      await flushPromises()

      const input = wrapper.find('input[type="text"]')
      await input.setValue('nonexistent')
      await flushPromises()

      expect(wrapper.text()).toContain('No simulations match your filters')
    })

    it('renders action links (Graph, Simulation, Report) for each run', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        { id: 'task-42', scenarioName: 'Test', totalRounds: 10, totalActions: 50, twitterActions: 25, redditActions: 25, status: 'completed', timestamp: Date.now() },
      ]

      const wrapper = mountSimulations()
      await flushPromises()

      expect(wrapper.text()).toContain('Graph')
      expect(wrapper.text()).toContain('Simulation')
      expect(wrapper.text()).toContain('Report')
    })
  })

  // ---------------------------------------------------------------------------
  // ScenarioBuilderView — loads scenario detail from store (API-backed)
  // ---------------------------------------------------------------------------
  describe('ScenarioBuilderView', () => {
    it('loads scenario data and pre-fills the form', async () => {
      global.fetch = vi.fn().mockResolvedValue(okJson({
        id: 'outbound_campaign',
        name: 'Outbound Campaign Pre-Testing',
        description: 'Simulate outbound emails.',
        seed_text: 'Intercom campaign copy...',
        agent_config: {
          count: 250,
          persona_types: ['VP of Support', 'CX Director'],
          firmographic_mix: { industries: ['SaaS', 'Fintech'] },
        },
        simulation_config: {
          total_hours: 48,
          minutes_per_round: 30,
          platform_mode: 'twitter',
        },
      }))

      const wrapper = mount(ScenarioBuilderView, {
        props: { id: 'outbound_campaign' },
        global: {
          stubs: { 'router-link': RouterLinkStub },
        },
      })
      await flushPromises()

      expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/gtm/scenarios/outbound_campaign'))
      expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
      const textarea = wrapper.find('textarea')
      expect(textarea.element.value).toBe('Intercom campaign copy...')
    })

    it('shows loading state while fetching scenario', () => {
      global.fetch = vi.fn(() => new Promise(() => {}))
      const wrapper = mount(ScenarioBuilderView, {
        props: { id: 'test' },
        global: { stubs: { 'router-link': RouterLinkStub } },
      })

      expect(wrapper.text()).toContain('Loading scenario...')
    })
  })

  // ---------------------------------------------------------------------------
  // ReportView — loads report from /api/report/check + /api/report/sections
  // ---------------------------------------------------------------------------
  describe('ReportView', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('loads completed report and renders section titles', async () => {
      let callIndex = 0
      global.fetch = vi.fn(async () => {
        const responses = [
          okJson({
            success: true,
            data: {
              simulation_id: 'sim-1',
              has_report: true,
              report_status: 'completed',
              report_id: 'rpt-1',
            },
          }),
          okJson({
            success: true,
            data: {
              report_id: 'rpt-1',
              sections: [
                { filename: 'section_01.md', section_index: 1, content: '## Executive Summary\n\nKey insights from the simulation.' },
                { filename: 'section_02.md', section_index: 2, content: '## Recommendations\n\nFocus on enterprise.' },
              ],
              total_sections: 2,
              is_complete: true,
            },
          }),
        ]
        return responses[callIndex++] || { ok: false, json: async () => ({}) }
      })

      const wrapper = mount(ReportView, {
        props: { taskId: 'sim-1' },
        global: { stubs: { 'router-link': RouterLinkStub } },
      })
      await flushPromises()

      expect(wrapper.text()).toContain('Executive Summary')
      expect(wrapper.text()).toContain('Recommendations')
    })

    it('shows generating state when no report exists yet', async () => {
      global.fetch = vi.fn(async () => ({ ok: false, status: 404, json: async () => ({ success: false }) }))

      const wrapper = mount(ReportView, {
        props: { taskId: 'sim-new' },
        global: { stubs: { 'router-link': RouterLinkStub } },
      })
      await flushPromises()

      expect(wrapper.text()).toContain('Generat')
    })
  })

  // ---------------------------------------------------------------------------
  // SimulationWorkspaceView — mounts and starts polling
  // ---------------------------------------------------------------------------
  describe('SimulationWorkspaceView', () => {
    function mountWorkspace(query = {}) {
      mockRoute = { params: {}, query: { tab: 'graph', ...query } }
      return mount(SimulationWorkspaceView, {
        props: { taskId: 'task-abc' },
        global: {
          stubs: {
            'router-link': RouterLinkStub,
            GraphPanel: { template: '<div class="graph-panel-stub">Graph</div>', props: ['taskId', 'demoMode'] },
            SimulationPanel: { template: '<div class="sim-panel-stub">Sim</div>', props: ['taskId'] },
            WorkspacePhaseNav: { template: '<div class="phase-nav-stub">Nav</div>', props: ['activeTab', 'taskId', 'polling'] },
          },
        },
      })
    }

    it('renders breadcrumbs and tab panels', async () => {
      const wrapper = mountWorkspace()
      await flushPromises()

      expect(wrapper.text()).toContain('Home')
      expect(wrapper.text()).toContain('Workspace')
      expect(wrapper.find('.graph-panel-stub').exists()).toBe(true)
      expect(wrapper.find('.sim-panel-stub').exists()).toBe(true)
    })

    it('starts polling on mount', async () => {
      mountWorkspace()
      await flushPromises()

      const pollingResult = useSimulationPolling.mock.results[0].value
      expect(pollingResult.start).toHaveBeenCalled()
    })

    it('stops polling on unmount', async () => {
      const wrapper = mountWorkspace()
      await flushPromises()

      const pollingResult = useSimulationPolling.mock.results[0].value
      wrapper.unmount()
      expect(pollingResult.stop).toHaveBeenCalled()
    })

    it('defaults to graph tab', async () => {
      const wrapper = mountWorkspace()
      await flushPromises()

      const graphPanel = wrapper.find('.graph-panel-stub')
      expect(graphPanel.isVisible()).toBe(true)
    })

    it('respects simulation tab from route query', async () => {
      const wrapper = mountWorkspace({ tab: 'simulation' })
      await flushPromises()

      const simPanel = wrapper.find('.sim-panel-stub')
      expect(simPanel.isVisible()).toBe(true)
    })
  })
})
