import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import CollaborationIndicator from '../CollaborationIndicator.vue'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

function makePolling(overrides = {}) {
  return {
    runStatus: ref(overrides.runStatus ?? null),
    simStatus: ref(overrides.simStatus ?? 'idle'),
    recentActions: ref(overrides.recentActions ?? []),
  }
}

function mountComponent(pollingOverrides = {}, isDemoMode = false) {
  return mount(CollaborationIndicator, {
    global: {
      provide: {
        polling: makePolling(pollingOverrides),
        demoMode: ref(isDemoMode),
      },
    },
  })
}

const runningActions = [
  { round_num: 5, agent_name: 'Alice, VP Sales @ Intercom', platform: 'twitter', action_type: 'POST' },
  { round_num: 5, agent_name: 'Bob, Engineer @ Corp', platform: 'reddit', action_type: 'REPLY' },
  { round_num: 4, agent_name: 'Carol, PM @ Startup', platform: 'twitter', action_type: 'POST' },
]

describe('CollaborationIndicator', () => {
  describe('hidden states', () => {
    it('hidden when no actions (empty state)', () => {
      const wrapper = mountComponent({ runStatus: { runner_status: 'running' }, recentActions: [] })
      expect(wrapper.find('.collab-indicator').exists()).toBe(false)
      wrapper.unmount()
    })

    it('hidden when only 1 agent in recent actions', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running' },
        recentActions: [
          { round_num: 5, agent_name: 'Alice, VP Sales @ Intercom', platform: 'twitter', action_type: 'POST' },
        ],
      })
      expect(wrapper.find('.collab-indicator').exists()).toBe(false)
      wrapper.unmount()
    })

    it('hidden when simulation is idle (not running)', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'idle' },
        recentActions: runningActions,
      })
      expect(wrapper.find('.collab-indicator').exists()).toBe(false)
      wrapper.unmount()
    })
  })

  describe('visible state', () => {
    it('visible when 2+ agents and simulation is running', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: runningActions,
      })
      expect(wrapper.find('.collab-indicator').exists()).toBe(true)
      wrapper.unmount()
    })

    it('shows "Live Collaboration" heading when visible', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: runningActions,
      })
      expect(wrapper.text()).toContain('Live Collaboration')
      wrapper.unmount()
    })

    it('shows correct agent count', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: runningActions,
      })
      expect(wrapper.text()).toContain('3 agents')
      wrapper.unmount()
    })

    it('shows agent name badges', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: runningActions,
      })
      expect(wrapper.text()).toContain('Alice')
      expect(wrapper.text()).toContain('Bob')
      expect(wrapper.text()).toContain('Carol')
      wrapper.unmount()
    })

    it('shows agent initials in avatar circles', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: runningActions,
      })
      const avatars = wrapper.findAll('.collab-avatar')
      expect(avatars.length).toBe(3)
      expect(avatars[0].text()).toBe('A')
      expect(avatars[1].text()).toBe('B')
      expect(avatars[2].text()).toBe('C')
      wrapper.unmount()
    })

    it('visible in demo mode when actions exist', () => {
      const wrapper = mountComponent({
        runStatus: null,
        recentActions: runningActions,
      }, true)
      expect(wrapper.find('.collab-indicator').exists()).toBe(true)
      wrapper.unmount()
    })

    it('shows discussion topic text', () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: runningActions,
      })
      expect(wrapper.text()).toContain('evaluating migration timelines')
      wrapper.unmount()
    })
  })

  describe('agent limit', () => {
    it('limits agents to 5 maximum', () => {
      const manyActions = [
        { round_num: 5, agent_name: 'A1, R1 @ C1', platform: 'twitter', action_type: 'POST' },
        { round_num: 5, agent_name: 'A2, R2 @ C2', platform: 'twitter', action_type: 'POST' },
        { round_num: 5, agent_name: 'A3, R3 @ C3', platform: 'twitter', action_type: 'POST' },
        { round_num: 5, agent_name: 'A4, R4 @ C4', platform: 'twitter', action_type: 'POST' },
        { round_num: 5, agent_name: 'A5, R5 @ C5', platform: 'twitter', action_type: 'POST' },
        { round_num: 5, agent_name: 'A6, R6 @ C6', platform: 'twitter', action_type: 'POST' },
        { round_num: 5, agent_name: 'A7, R7 @ C7', platform: 'twitter', action_type: 'POST' },
      ]
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: manyActions,
      })
      const avatars = wrapper.findAll('.collab-avatar')
      expect(avatars.length).toBe(5)
      wrapper.unmount()
    })
  })

  describe('topic rotation', () => {
    it('rotates discussion topics every 4 seconds', async () => {
      const wrapper = mountComponent({
        runStatus: { runner_status: 'running', current_round: 5 },
        recentActions: runningActions,
      })
      expect(wrapper.text()).toContain('evaluating migration timelines')

      vi.advanceTimersByTime(4000)
      await nextTick()

      expect(wrapper.text()).toContain('comparing support platform costs')
      wrapper.unmount()
    })
  })
})
