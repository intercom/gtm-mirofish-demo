import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import AgentMoodIndicator from '../AgentMoodIndicator.vue'

beforeEach(() => {
  vi.stubGlobal('ResizeObserver', class {
    observe() {}
    disconnect() {}
    unobserve() {}
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function makeAction(agentName, content, round = 1) {
  return {
    round_num: round,
    agent_name: agentName,
    action_type: 'CREATE_POST',
    action_args: { content },
  }
}

function getTitle(wrapper) {
  return wrapper.find('.inline-flex').attributes('title')
}

describe('AgentMoodIndicator', () => {
  describe('mood computation from score prop', () => {
    it('shows neutral mood (score 5) when no props', () => {
      const wrapper = mount(AgentMoodIndicator)
      expect(getTitle(wrapper)).toContain('Neutral')
      expect(getTitle(wrapper)).toContain('5/10')
      wrapper.unmount()
    })

    it('uses score prop directly when provided (score=9 -> Enthusiastic)', () => {
      const wrapper = mount(AgentMoodIndicator, { props: { score: 9 } })
      expect(getTitle(wrapper)).toContain('Enthusiastic')
      expect(getTitle(wrapper)).toContain('9/10')
      wrapper.unmount()
    })

    it('uses score prop for low score (score=2 -> Frustrated)', () => {
      const wrapper = mount(AgentMoodIndicator, { props: { score: 2 } })
      expect(getTitle(wrapper)).toContain('Frustrated')
      expect(getTitle(wrapper)).toContain('2/10')
      wrapper.unmount()
    })

    it('uses score prop for mid score (score=4 -> Skeptical)', () => {
      const wrapper = mount(AgentMoodIndicator, { props: { score: 4 } })
      expect(getTitle(wrapper)).toContain('Skeptical')
      expect(getTitle(wrapper)).toContain('4/10')
      wrapper.unmount()
    })

    it('uses score prop for moderate score (score=7 -> Engaged)', () => {
      const wrapper = mount(AgentMoodIndicator, { props: { score: 7 } })
      expect(getTitle(wrapper)).toContain('Engaged')
      expect(getTitle(wrapper)).toContain('7/10')
      wrapper.unmount()
    })

    it('clamps score to 1-10 range', () => {
      const low = mount(AgentMoodIndicator, { props: { score: -5 } })
      expect(getTitle(low)).toContain('1/10')
      low.unmount()

      const high = mount(AgentMoodIndicator, { props: { score: 99 } })
      expect(getTitle(high)).toContain('10/10')
      high.unmount()
    })
  })

  describe('SVG face rendering', () => {
    it('shows SVG face element', () => {
      const wrapper = mount(AgentMoodIndicator)
      expect(wrapper.find('svg').exists()).toBe(true)
      wrapper.unmount()
    })
  })

  describe('size modes', () => {
    it('shows mood label in large size mode', () => {
      const wrapper = mount(AgentMoodIndicator, { props: { size: 'large', score: 7 } })
      expect(wrapper.find('span').text()).toBe('Engaged')
      wrapper.unmount()
    })

    it('hides mood label in compact mode', () => {
      const wrapper = mount(AgentMoodIndicator, { props: { size: 'compact', score: 7 } })
      const spans = wrapper.findAll('span')
      const labelSpan = spans.find(s => s.text() === 'Engaged')
      expect(labelSpan).toBeUndefined()
      wrapper.unmount()
    })
  })

  describe('mood from actions', () => {
    it('computes positive mood from positive content in actions', () => {
      const actions = [
        makeAction('Alice', 'impressive innovative excellent amazing love'),
        makeAction('Alice', 'compelling great benefit promising exciting'),
      ]
      const wrapper = mount(AgentMoodIndicator, { props: { actions, agentName: 'Alice' } })
      expect(getTitle(wrapper)).toMatch(/Enthusiastic|Engaged/)
      wrapper.unmount()
    })

    it('computes negative mood from negative content in actions', () => {
      const actions = [
        makeAction('Bob', 'concerned skeptical expensive complex difficult'),
        makeAction('Bob', 'worried frustrated poor slow confusing'),
      ]
      const wrapper = mount(AgentMoodIndicator, { props: { actions, agentName: 'Bob' } })
      expect(getTitle(wrapper)).toMatch(/Frustrated|Skeptical/)
      wrapper.unmount()
    })

    it('filters actions by agentName when provided', () => {
      const actions = [
        makeAction('Alice', 'impressive excellent amazing innovative'),
        makeAction('Bob', 'concerned skeptical expensive complex'),
      ]
      const wrapper = mount(AgentMoodIndicator, { props: { actions, agentName: 'Alice' } })
      expect(getTitle(wrapper)).toMatch(/Enthusiastic|Engaged/)
      wrapper.unmount()
    })
  })

  describe('title attribute', () => {
    it('contains mood label and score', () => {
      const wrapper = mount(AgentMoodIndicator, { props: { score: 6 } })
      expect(getTitle(wrapper)).toBe('Neutral (6/10)')
      wrapper.unmount()
    })
  })
})
