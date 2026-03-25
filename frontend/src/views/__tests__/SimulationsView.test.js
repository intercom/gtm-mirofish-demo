import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import SimulationsView from '../SimulationsView.vue'
import { useSimulationStore } from '../../stores/simulation'

function makeRun(overrides = {}) {
  return {
    id: 'run-1',
    scenarioId: 'outbound_campaign',
    scenarioName: 'Outbound Campaign Pre-Testing',
    seedText: 'Test seed text',
    agentCount: 200,
    personas: ['VP of Support'],
    industries: ['SaaS'],
    duration: 72,
    platformMode: 'parallel',
    totalRounds: 144,
    totalActions: 1200,
    twitterActions: 700,
    redditActions: 500,
    status: 'completed',
    timestamp: Date.now() - 60000,
    ...overrides,
  }
}

function mountView() {
  return mount(SimulationsView, {
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        Teleport: { template: '<div><slot /></div>' },
      },
    },
  })
}

describe('SimulationsView — Dashboard Data Display', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    })
  })

  describe('empty state', () => {
    it('shows empty state when no runs exist', () => {
      const wrapper = mountView()
      expect(wrapper.text()).toContain('No simulation runs yet')
      expect(wrapper.text()).toContain('Run your first simulation')
    })

    it('does not show summary stats when empty', () => {
      const wrapper = mountView()
      expect(wrapper.text()).not.toContain('Total Runs')
      expect(wrapper.text()).not.toContain('Total Actions')
      expect(wrapper.text()).not.toContain('Top Scenario')
    })

    it('does not show search/filter bar when empty', () => {
      const wrapper = mountView()
      expect(wrapper.find('input[placeholder*="Search"]').exists()).toBe(false)
    })

    it('does not show Clear All button when empty', () => {
      const wrapper = mountView()
      const clearBtn = wrapper.findAll('button').find(b => b.text() === 'Clear All')
      expect(clearBtn).toBeUndefined()
    })
  })

  describe('summary stats', () => {
    it('shows total runs count', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Pricing Change Simulation' }))

      const wrapper = mountView()
      expect(wrapper.text()).toContain('Total Runs')
      expect(wrapper.text()).toContain('2')
    })

    it('shows aggregated total actions across all runs', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', totalActions: 500 }))
      store.addSessionRun(makeRun({ id: 'r2', totalActions: 300 }))

      const wrapper = mountView()
      expect(wrapper.text()).toContain('Total Actions')
      expect(wrapper.text()).toContain('800')
    })

    it('shows the most frequently used scenario name', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Outbound Campaign Pre-Testing' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Outbound Campaign Pre-Testing' }))
      store.addSessionRun(makeRun({ id: 'r3', scenarioName: 'Pricing Change Simulation' }))

      const wrapper = mountView()
      expect(wrapper.text()).toContain('Top Scenario')
      expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
    })

    it('shows run count badge in header', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1' }))
      store.addSessionRun(makeRun({ id: 'r2' }))

      const wrapper = mountView()
      const badge = wrapper.find('.rounded-full')
      expect(badge.text()).toBe('2')
    })
  })

  describe('run cards', () => {
    it('renders a card for each run', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Outbound Campaign Pre-Testing' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Pricing Change Simulation' }))

      const wrapper = mountView()
      expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
      expect(wrapper.text()).toContain('Pricing Change Simulation')
    })

    it('displays rounds and actions metrics on each card', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', totalRounds: 144, totalActions: 1200 }))

      const wrapper = mountView()
      expect(wrapper.text()).toContain('Rounds')
      expect(wrapper.text()).toContain('144')
      expect(wrapper.text()).toContain('Actions')
      expect(wrapper.text()).toContain('1200')
    })

    it('displays twitter and reddit action counts', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', twitterActions: 700, redditActions: 500 }))

      const wrapper = mountView()
      expect(wrapper.text()).toContain('Twitter')
      expect(wrapper.text()).toContain('700')
      expect(wrapper.text()).toContain('Reddit')
      expect(wrapper.text()).toContain('500')
    })

    it('shows Completed status badge for completed runs', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', status: 'completed' }))

      const wrapper = mountView()
      const badges = wrapper.findAll('.rounded-full')
      const statusBadge = badges.find(b => b.text() === 'Completed')
      expect(statusBadge).toBeTruthy()
    })

    it('shows In Progress badge for running simulations', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', status: 'running' }))

      const wrapper = mountView()
      const badges = wrapper.findAll('.rounded-full')
      const statusBadge = badges.find(b => b.text() === 'In Progress')
      expect(statusBadge).toBeTruthy()
    })

    it('shows Failed badge for errored simulations', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', status: 'failed' }))

      const wrapper = mountView()
      const badges = wrapper.findAll('.rounded-full')
      const statusBadge = badges.find(b => b.text() === 'Failed')
      expect(statusBadge).toBeTruthy()
    })

    it('renders Graph, Simulation, and Report action links', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1' }))

      const wrapper = mountView()
      const links = wrapper.findAll('a')
      const linkTexts = links.map(l => l.text())
      expect(linkTexts).toContain('Graph')
      expect(linkTexts).toContain('Simulation')
      expect(linkTexts).toContain('Report')
    })

    it('shows Re-run link when scenarioId and seedText are present', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioId: 'outbound_campaign', seedText: 'some text' }))

      const wrapper = mountView()
      const rerunLink = wrapper.findAll('a').find(l => l.text().includes('Re-run'))
      expect(rerunLink).toBeTruthy()
    })

    it('hides Re-run link when scenarioId is missing', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioId: null, seedText: null }))

      const wrapper = mountView()
      const rerunLink = wrapper.findAll('a').find(l => l.text().includes('Re-run'))
      expect(rerunLink).toBeUndefined()
    })

    it('shows relative and absolute timestamps', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', timestamp: Date.now() - 30000 }))

      const wrapper = mountView()
      expect(wrapper.text()).toContain('just now')
    })
  })

  describe('search filtering', () => {
    it('filters runs by scenario name search', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Alpha Campaign' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Beta Simulation' }))

      const wrapper = mountView()
      const input = wrapper.find('input[placeholder*="Search"]')
      await input.setValue('Beta')

      const cards = wrapper.findAll('h3')
      expect(cards).toHaveLength(1)
      expect(cards[0].text()).toBe('Beta Simulation')
    })

    it('shows no-results message when search matches nothing', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1' }))

      const wrapper = mountView()
      const input = wrapper.find('input[placeholder*="Search"]')
      await input.setValue('nonexistent')

      expect(wrapper.text()).toContain('No simulations match your filters')
    })

    it('provides a Clear filters link when no results match', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1' }))

      const wrapper = mountView()
      const input = wrapper.find('input[placeholder*="Search"]')
      await input.setValue('nonexistent')

      const clearBtn = wrapper.findAll('button').find(b => b.text() === 'Clear filters')
      expect(clearBtn).toBeTruthy()
    })

    it('clear filters resets search and status filter', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Outbound Campaign Pre-Testing' }))

      const wrapper = mountView()
      const input = wrapper.find('input[placeholder*="Search"]')
      await input.setValue('nonexistent')

      const clearBtn = wrapper.findAll('button').find(b => b.text() === 'Clear filters')
      await clearBtn.trigger('click')

      expect(wrapper.text()).toContain('Outbound Campaign Pre-Testing')
    })
  })

  describe('status filtering', () => {
    it('filters by completed status', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Run A', status: 'completed' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Run B', status: 'running' }))

      const wrapper = mountView()
      const select = wrapper.findAll('select')[0]
      await select.setValue('completed')

      expect(wrapper.text()).toContain('Run A')
      expect(wrapper.text()).not.toContain('Run B')
    })

    it('filters by in_progress status', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Alpha Done', status: 'completed' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Beta Building', status: 'building_graph' }))

      const wrapper = mountView()
      const select = wrapper.findAll('select')[0]
      await select.setValue('in_progress')

      const cards = wrapper.findAll('h3')
      expect(cards).toHaveLength(1)
      expect(cards[0].text()).toBe('Beta Building')
    })

    it('shows all runs when filter is set to all', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Run A', status: 'completed' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Run B', status: 'failed' }))

      const wrapper = mountView()
      const select = wrapper.findAll('select')[0]
      await select.setValue('all')

      expect(wrapper.text()).toContain('Run A')
      expect(wrapper.text()).toContain('Run B')
    })
  })

  describe('sorting', () => {
    it('sorts newest first by default', () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        makeRun({ id: 'r1', scenarioName: 'Older', timestamp: 1000 }),
        makeRun({ id: 'r2', scenarioName: 'Newer', timestamp: 2000 }),
      ]

      const wrapper = mountView()
      const cards = wrapper.findAll('h3')
      expect(cards[0].text()).toBe('Newer')
      expect(cards[1].text()).toBe('Older')
    })

    it('sorts oldest first when selected', async () => {
      const store = useSimulationStore()
      store.sessionRuns = [
        makeRun({ id: 'r1', scenarioName: 'Older', timestamp: 1000 }),
        makeRun({ id: 'r2', scenarioName: 'Newer', timestamp: 2000 }),
      ]

      const wrapper = mountView()
      const sortSelect = wrapper.findAll('select')[1]
      await sortSelect.setValue('oldest')

      const cards = wrapper.findAll('h3')
      expect(cards[0].text()).toBe('Older')
      expect(cards[1].text()).toBe('Newer')
    })

    it('sorts by most actions when selected', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Few', totalActions: 50 }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Many', totalActions: 999 }))

      const wrapper = mountView()
      const sortSelect = wrapper.findAll('select')[1]
      await sortSelect.setValue('most_actions')

      const cards = wrapper.findAll('h3')
      expect(cards[0].text()).toBe('Many')
      expect(cards[1].text()).toBe('Few')
    })

    it('sorts by most rounds when selected', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Short', totalRounds: 10 }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Long', totalRounds: 300 }))

      const wrapper = mountView()
      const sortSelect = wrapper.findAll('select')[1]
      await sortSelect.setValue('most_rounds')

      const cards = wrapper.findAll('h3')
      expect(cards[0].text()).toBe('Long')
      expect(cards[1].text()).toBe('Short')
    })
  })

  describe('delete and clear', () => {
    it('removes a run when delete is confirmed', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', scenarioName: 'Run A' }))
      store.addSessionRun(makeRun({ id: 'r2', scenarioName: 'Run B' }))

      const wrapper = mountView()
      const deleteButtons = wrapper.findAll('button[title="Delete run"]')
      await deleteButtons[0].trigger('click')

      const confirmBtn = wrapper.findAll('button').find(b => b.text() === 'Delete')
      await confirmBtn.trigger('click')

      expect(wrapper.text()).not.toContain('Run A')
      expect(wrapper.text()).toContain('Run B')
    })

    it('clears all runs when Clear All is confirmed', async () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1' }))
      store.addSessionRun(makeRun({ id: 'r2' }))

      const wrapper = mountView()
      const clearAllBtn = wrapper.findAll('button').find(b => b.text() === 'Clear All')
      await clearAllBtn.trigger('click')

      // The dialog's confirm button is the last "Clear All" button (inside the dialog)
      const allClearBtns = wrapper.findAll('button').filter(b => b.text() === 'Clear All')
      const dialogConfirmBtn = allClearBtns[allClearBtns.length - 1]
      await dialogConfirmBtn.trigger('click')

      expect(store.sessionRuns).toHaveLength(0)
    })
  })

  describe('status normalization', () => {
    it('normalizes "complete" to Completed label', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', status: 'complete' }))

      const wrapper = mountView()
      const badges = wrapper.findAll('.rounded-full')
      const statusBadge = badges.find(b => b.text() === 'Completed')
      expect(statusBadge).toBeTruthy()
    })

    it('normalizes "error" to Failed label', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', status: 'error' }))

      const wrapper = mountView()
      const badges = wrapper.findAll('.rounded-full')
      const statusBadge = badges.find(b => b.text() === 'Failed')
      expect(statusBadge).toBeTruthy()
    })

    it('normalizes "building_graph" to In Progress label', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', status: 'building_graph' }))

      const wrapper = mountView()
      const badges = wrapper.findAll('.rounded-full')
      const statusBadge = badges.find(b => b.text() === 'In Progress')
      expect(statusBadge).toBeTruthy()
    })

    it('normalizes null/undefined status to Completed', () => {
      const store = useSimulationStore()
      store.addSessionRun(makeRun({ id: 'r1', status: null }))

      const wrapper = mountView()
      const badges = wrapper.findAll('.rounded-full')
      const statusBadge = badges.find(b => b.text() === 'Completed')
      expect(statusBadge).toBeTruthy()
    })
  })
})
