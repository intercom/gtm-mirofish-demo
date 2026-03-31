import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import SimulationProgressBar from '../SimulationProgressBar.vue'

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

function mountProgressBar(props = {}, pollingOverrides = {}) {
  const polling = makePolling(pollingOverrides)
  return mount(SimulationProgressBar, {
    props: { taskId: 'task-abc', ...props },
    global: {
      provide: { polling },
    },
  })
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('SimulationProgressBar', () => {
  describe('progress bar', () => {
    it('renders progress bar with correct width percentage', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 45, current_round: 5, total_rounds: 10 },
        simStatus: 'running',
      })
      const bar = wrapper.find('.rounded-full.transition-all')
      expect(bar.attributes('style')).toContain('width: 45%')
    })

    it('uses success color for completed status', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'completed', progress_percent: 100, current_round: 10, total_rounds: 10 },
        simStatus: 'completed',
      })
      const bar = wrapper.find('.rounded-full.transition-all')
      expect(bar.classes()).toContain('bg-[var(--color-success)]')
    })

    it('uses primary color for running status', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 50, current_round: 5, total_rounds: 10 },
        simStatus: 'running',
      })
      const bar = wrapper.find('.rounded-full.transition-all')
      expect(bar.classes()).toContain('bg-[var(--color-primary)]')
    })
  })

  describe('text info', () => {
    it('shows round and percentage text', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 42, current_round: 3, total_rounds: 8 },
        simStatus: 'running',
      })
      expect(wrapper.text()).toContain('Round 3/8')
      expect(wrapper.text()).toContain('42%')
    })

    it('displays elapsed time starting at 0:00', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 0, current_round: 0, total_rounds: 10 },
        simStatus: 'running',
      })
      expect(wrapper.text()).toContain('0:00')
    })
  })

  describe('agent indicators', () => {
    it('shows agent initials from recent actions', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 50, current_round: 3, total_rounds: 10 },
        simStatus: 'running',
        recentActions: [
          { agent_name: 'Alice' },
          { agent_name: 'Bob' },
        ],
      })
      expect(wrapper.text()).toContain('A')
      expect(wrapper.text()).toContain('B')
    })

    it('shows correct agent count', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 50, current_round: 3, total_rounds: 10 },
        simStatus: 'running',
        recentActions: [
          { agent_name: 'Alice' },
          { agent_name: 'Bob' },
          { agent_name: 'Charlie' },
        ],
      })
      expect(wrapper.text()).toContain('3 active')
    })

    it('limits agent indicators to 8', () => {
      const actions = Array.from({ length: 12 }, (_, i) => ({ agent_name: `Agent${i}` }))
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 50, current_round: 3, total_rounds: 10 },
        simStatus: 'running',
        recentActions: actions,
      })
      const indicators = wrapper.findAll('.w-5.h-5.rounded-full')
      expect(indicators.length).toBe(8)
    })
  })

  describe('status indicators', () => {
    it('shows pulse dot when running', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 50, current_round: 5, total_rounds: 10 },
        simStatus: 'running',
      })
      const pulse = wrapper.find('.animate-pulse')
      expect(pulse.exists()).toBe(true)
    })

    it('shows pulse dot when building', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: null,
        simStatus: 'building',
      })
      const pulse = wrapper.find('.animate-pulse')
      expect(pulse.exists()).toBe(true)
    })

    it('shows "Complete" text when completed', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'completed', progress_percent: 100, current_round: 10, total_rounds: 10 },
        simStatus: 'completed',
      })
      expect(wrapper.text()).toContain('Complete')
    })

    it('shows "Failed" text when failed', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'failed', progress_percent: 30, current_round: 3, total_rounds: 10 },
        simStatus: 'failed',
      })
      expect(wrapper.text()).toContain('Failed')
    })

    it('no pulse dot when completed', () => {
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'completed', progress_percent: 100, current_round: 10, total_rounds: 10 },
        simStatus: 'completed',
      })
      const pulse = wrapper.find('.animate-pulse')
      expect(pulse.exists()).toBe(false)
    })
  })

  describe('timer cleanup', () => {
    it('clears timer on unmount (no leaks)', () => {
      const clearSpy = vi.spyOn(globalThis, 'clearInterval')
      const wrapper = mountProgressBar({}, {
        runStatus: { runner_status: 'running', progress_percent: 50, current_round: 5, total_rounds: 10 },
        simStatus: 'running',
      })
      wrapper.unmount()
      expect(clearSpy).toHaveBeenCalled()
    })
  })
})
