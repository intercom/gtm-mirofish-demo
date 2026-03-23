import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SimulationView from './SimulationView.vue'

const mockStatus = {
  success: true,
  data: {
    runner_status: 'running',
    current_round: 3,
    total_rounds: 24,
    progress_percent: 12.5,
    total_actions_count: 42,
  },
}

const mockActions = {
  success: true,
  data: [
    { round_num: 3, platform: 'twitter', agent_id: 1, agent_name: 'VP of Support', action_type: 'REPLY_POST', action_args: { content: 'Good thread' }, success: true },
    { round_num: 2, platform: 'reddit', agent_id: 2, agent_name: 'CX Director', action_type: 'LIKE_POST', action_args: {}, success: true },
    { round_num: 1, platform: 'twitter', agent_id: 3, agent_name: 'Sales Rep', action_type: 'CREATE_POST', action_args: { content: 'New quarter' }, success: true },
    { round_num: 1, platform: 'twitter', agent_id: 1, agent_name: 'VP of Support', action_type: 'REPOST', action_args: {}, success: true },
  ],
}

function setupFetchMock() {
  global.fetch = vi.fn((url) => {
    if (url.includes('/run-status')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockStatus) })
    }
    if (url.includes('/actions')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockActions) })
    }
    return Promise.resolve({ ok: false })
  })
}

async function mountAndFlush(props = {}) {
  const wrapper = mount(SimulationView, {
    props: { taskId: 'test-456', ...props },
    global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
  })
  await flushPromises()
  return wrapper
}

describe('SimulationView', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    setupFetchMock()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('renders with running status', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('Live Simulation')
    expect(wrapper.text()).toContain('test-456')
    expect(wrapper.text()).toContain('Running')
  })

  it('renders all metric cards', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('Total Actions')
    expect(wrapper.text()).toContain('Replies')
    expect(wrapper.text()).toContain('Likes')
    expect(wrapper.text()).toContain('Reposts')
    expect(wrapper.text()).toContain('Current Round')
  })

  it('displays metric labels and values', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).toContain('Total Actions')
    expect(wrapper.text()).toContain('Round 3 of 24')
  })

  it('renders activity feed with agent actions', async () => {
    const wrapper = await mountAndFlush()
    expect(wrapper.text()).toContain('Agent Activity Feed')
    expect(wrapper.text()).toContain('VP of Support')
    expect(wrapper.text()).toContain('replied')
    expect(wrapper.text()).toContain('Good thread')
  })
})
