import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import SimulationView from './SimulationView.vue'

vi.mock('../services/api.js', () => ({
  createSimulation: vi.fn().mockResolvedValue({ data: { simulation_id: 'sim-1' } }),
  prepareSimulation: vi.fn().mockResolvedValue({ data: { already_prepared: true } }),
  getPrepareStatus: vi.fn(),
  startSimulation: vi.fn().mockResolvedValue({}),
  getRunStatus: vi.fn().mockResolvedValue({
    data: {
      current_round: 3,
      total_rounds: 10,
      total_actions_count: 47,
      reddit_actions_count: 20,
      twitter_actions_count: 27,
      progress_percent: 30,
      runner_status: 'running',
    },
  }),
  getSimulationActions: vi.fn().mockResolvedValue({ data: { actions: [] } }),
  pollTask: vi.fn(),
}))

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/simulation/:taskId',
        component: SimulationView,
        props: true,
      },
      { path: '/report/:taskId', component: { template: '<div />' } },
    ],
  })
}

describe('SimulationView', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  async function mountView() {
    const router = createTestRouter()
    await router.push('/simulation/test-456?projectId=p1&graphId=g1')
    await router.isReady()
    const wrapper = mount(SimulationView, {
      props: { taskId: 'test-456' },
      global: { plugins: [router] },
    })
    await flushPromises()
    return wrapper
  }

  it('renders header after API resolves', async () => {
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('Live Simulation')
    expect(wrapper.text()).toContain('sim-1')
  })

  it('displays metric labels', async () => {
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('Total Actions')
    expect(wrapper.text()).toContain('Reddit Actions')
    expect(wrapper.text()).toContain('Twitter Actions')
    expect(wrapper.text()).toContain('Round')
  })

  it('renders count-up metric elements with data-testid', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('[data-testid="metric-actions"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="metric-replies"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="metric-likes"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="metric-round"]').exists()).toBe(true)
  })

  it('metrics start at 0 from count-up composable', async () => {
    const wrapper = await mountView()
    const actions = wrapper.find('[data-testid="metric-actions"]')
    // useCountUp animates via requestAnimationFrame, starts at 0
    expect(actions.text()).toBe('0')
  })

  it('renders activity feed section', async () => {
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('Agent Activity Feed')
  })
})
