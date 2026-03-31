import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import SimulationControls from '../SimulationControls.vue'

function makePolling(overrides = {}) {
  return {
    graphStatus: ref(overrides.graphStatus ?? 'complete'),
    graphProgress: ref(overrides.graphProgress ?? 100),
    graphData: ref(overrides.graphData ?? { nodes: [], edges: [] }),
    graphId: ref(overrides.graphId ?? 'g-1'),
    graphTask: ref(overrides.graphTask ?? null),
    isDemoFallback: ref(overrides.isDemoFallback ?? false),
    runStatus: ref(overrides.runStatus ?? null),
    simStatus: ref(overrides.simStatus ?? 'idle'),
    recentActions: ref(overrides.recentActions ?? []),
    timeline: ref(overrides.timeline ?? []),
  }
}

function mountControls(props = {}, pollingOverrides = {}) {
  const polling = makePolling(pollingOverrides)
  return mount(SimulationControls, {
    props: { taskId: 'task-abc', ...props },
    global: {
      provide: { polling },
      stubs: {
        RouterLink: { template: '<a :to="to"><slot /></a>', props: ['to'] },
      },
    },
  })
}

describe('SimulationControls', () => {
  describe('status badge', () => {
    it('shows "Preparing" for null runStatus', () => {
      const wrapper = mountControls({}, { runStatus: null })
      expect(wrapper.text()).toContain('Preparing')
    })

    it('shows "Preparing" for idle runner_status', () => {
      const wrapper = mountControls({}, { runStatus: { runner_status: 'idle' } })
      expect(wrapper.text()).toContain('Preparing')
    })

    it('shows "Preparing" for starting runner_status', () => {
      const wrapper = mountControls({}, { runStatus: { runner_status: 'starting' } })
      expect(wrapper.text()).toContain('Preparing')
    })

    it('shows "Running" for running runner_status', () => {
      const wrapper = mountControls({}, { runStatus: { runner_status: 'running' } })
      expect(wrapper.text()).toContain('Running')
    })

    it('shows "Completed" for completed runner_status', () => {
      const wrapper = mountControls({}, { runStatus: { runner_status: 'completed' } })
      expect(wrapper.text()).toContain('Completed')
    })

    it('shows "Failed" for failed runner_status', () => {
      const wrapper = mountControls({}, { runStatus: { runner_status: 'failed' } })
      expect(wrapper.text()).toContain('Failed')
    })
  })

  describe('round counter', () => {
    it('displays round counter from runStatus', () => {
      const wrapper = mountControls({}, {
        runStatus: { runner_status: 'running', current_round: 5, total_rounds: 24 },
      })
      expect(wrapper.text()).toContain('5 / 24')
    })
  })

  describe('action counts', () => {
    it('displays total actions count', () => {
      const wrapper = mountControls({}, {
        runStatus: { runner_status: 'running', total_actions_count: 150 },
      })
      expect(wrapper.text()).toContain('150')
      expect(wrapper.text()).toContain('Total')
    })

    it('displays twitter actions count', () => {
      const wrapper = mountControls({}, {
        runStatus: { runner_status: 'running', twitter_actions_count: 80 },
      })
      expect(wrapper.text()).toContain('80')
      expect(wrapper.text()).toContain('Twitter')
    })

    it('displays reddit actions count', () => {
      const wrapper = mountControls({}, {
        runStatus: { runner_status: 'running', reddit_actions_count: 70 },
      })
      expect(wrapper.text()).toContain('70')
      expect(wrapper.text()).toContain('Reddit')
    })

    it('shows zero values when runStatus is null', () => {
      const wrapper = mountControls({}, { runStatus: null })
      const text = wrapper.text()
      expect(text).toContain('0 / 0')
    })
  })

  describe('report link', () => {
    it('shows Generate Report link when completed', () => {
      const wrapper = mountControls({ taskId: 'task-99' }, {
        runStatus: { runner_status: 'completed' },
      })
      expect(wrapper.text()).toContain('Generate Report')
    })

    it('report link routes to /report/{taskId}', () => {
      const wrapper = mountControls({ taskId: 'task-99' }, {
        runStatus: { runner_status: 'completed' },
      })
      const link = wrapper.find('a')
      expect(link.attributes('to')).toBe('/report/task-99')
    })

    it('hides Generate Report when not completed', () => {
      const wrapper = mountControls({}, {
        runStatus: { runner_status: 'running' },
      })
      expect(wrapper.text()).not.toContain('Generate Report')
    })
  })

  describe('heading', () => {
    it('shows "Controls" heading', () => {
      const wrapper = mountControls()
      expect(wrapper.find('h3').text()).toBe('Controls')
    })
  })
})
