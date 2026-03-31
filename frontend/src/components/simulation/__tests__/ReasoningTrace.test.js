import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ReasoningTrace from '../ReasoningTrace.vue'

const fullTrace = {
  thought: 'I need to respond to this product launch tweet.',
  observation: 'The tweet has positive sentiment and high engagement.',
  inference: 'Engaging early could boost our visibility.\nAssumption: The audience is receptive to competitor commentary.',
  decision: 'Reply with a supportive comment.',
  justification: 'Aligning with the positive sentiment will build goodwill.',
  confidence: { thought: 0.9, observation: 0.75, inference: 0.5, decision: 0.85, justification: 0.6 },
}

describe('ReasoningTrace', () => {
  it('renders message in clean (default) view', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { message: 'Replied to tweet', trace: fullTrace },
    })
    expect(wrapper.text()).toContain('Replied to tweet')
  })

  it('defaults to clean view — hides reasoning sections', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { message: 'Replied to tweet', trace: fullTrace },
    })
    expect(wrapper.text()).not.toContain('Thought')
    expect(wrapper.text()).not.toContain('Observation')
  })

  it('shows toggle button when trace data exists', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { message: 'Test', trace: fullTrace },
    })
    expect(wrapper.text()).toContain('Clean')
  })

  it('does not show toggle button when no trace data', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { message: 'Test', trace: {} },
    })
    const buttons = wrapper.findAll('button')
    const toggleBtn = buttons.find(b => b.text().includes('Clean') || b.text().includes('Transparent'))
    expect(toggleBtn).toBeUndefined()
  })

  it('switches to transparent view on toggle click', async () => {
    const wrapper = mount(ReasoningTrace, {
      props: { message: 'Replied', trace: fullTrace },
    })
    const toggleBtn = wrapper.findAll('button').find(b => b.text().includes('Clean'))
    await toggleBtn.trigger('click')
    expect(wrapper.text()).toContain('Transparent')
    expect(wrapper.text()).toContain('Thought')
    expect(wrapper.text()).toContain('Observation')
    expect(wrapper.text()).toContain('Inference')
    expect(wrapper.text()).toContain('Decision')
    expect(wrapper.text()).toContain('Justification')
  })

  it('starts in transparent view when defaultTransparent is true', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { message: 'Test', trace: fullTrace, defaultTransparent: true },
    })
    expect(wrapper.text()).toContain('Transparent')
    expect(wrapper.text()).toContain('Thought')
  })

  it('renders all 5 reasoning sections in transparent mode', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { trace: fullTrace, defaultTransparent: true },
    })
    expect(wrapper.text()).toContain('Thought')
    expect(wrapper.text()).toContain('Observation')
    expect(wrapper.text()).toContain('Inference')
    expect(wrapper.text()).toContain('Decision')
    expect(wrapper.text()).toContain('Justification')
  })

  it('shows confidence indicators', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { trace: fullTrace, defaultTransparent: true },
    })
    expect(wrapper.text()).toContain('90%')
    expect(wrapper.text()).toContain('High')
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('Medium')
  })

  it('renders thought section in italic', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { trace: fullTrace, defaultTransparent: true },
    })
    const italicEl = wrapper.find('.italic')
    expect(italicEl.exists()).toBe(true)
    expect(italicEl.text()).toContain('I need to respond')
  })

  it('highlights assumptions with warning styling', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { trace: fullTrace, defaultTransparent: true },
    })
    expect(wrapper.text()).toContain('The audience is receptive to competitor commentary')
  })

  it('only renders sections that have content', () => {
    const partial = { thought: 'Thinking...', decision: 'Act now.' }
    const wrapper = mount(ReasoningTrace, {
      props: { trace: partial, defaultTransparent: true },
    })
    expect(wrapper.text()).toContain('Thought')
    expect(wrapper.text()).toContain('Decision')
    expect(wrapper.text()).not.toContain('Observation')
    expect(wrapper.text()).not.toContain('Inference')
    expect(wrapper.text()).not.toContain('Justification')
  })

  it('collapses a section when its header is clicked', async () => {
    const wrapper = mount(ReasoningTrace, {
      props: { trace: fullTrace, defaultTransparent: true },
    })
    const sectionBtns = wrapper.findAll('button').filter(b => b.text().includes('Thought'))
    expect(sectionBtns.length).toBeGreaterThan(0)
    await sectionBtns[0].trigger('click')
    // Chevron should rotate (no longer has rotate-180 class, since it was expanded before)
    const chevron = sectionBtns[0].find('svg:last-of-type')
    expect(chevron.classes()).not.toContain('rotate-180')
  })

  it('renders agent name when provided', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { agentName: 'Alice, PM @ Intercom', message: 'Test', trace: fullTrace },
    })
    expect(wrapper.text()).toContain('Alice, PM @ Intercom')
  })

  it('shows empty state when transparent with no trace sections', () => {
    const wrapper = mount(ReasoningTrace, {
      props: { trace: {}, defaultTransparent: true },
    })
    expect(wrapper.text()).toContain('No reasoning trace available')
  })
})
