import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChatView from '../ChatView.vue'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import axios from 'axios'

function mountChat(taskId = 'sim_test123') {
  return mount(ChatView, {
    props: { taskId },
    global: {
      stubs: { RouterLink: true },
    },
  })
}

describe('ChatView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    axios.get.mockResolvedValue({
      data: { success: true, data: { runner_status: 'running', current_round: 5, total_rounds: 24 } },
    })
  })

  it('renders empty state when no messages', () => {
    const wrapper = mountChat()
    expect(wrapper.text()).toContain('Chat with the Simulation')
    expect(wrapper.text()).toContain('Ask follow-up questions')
  })

  it('shows context indicator with simulation ID', () => {
    const wrapper = mountChat('sim_abc')
    expect(wrapper.text()).toContain('MiroFish Chat')
    expect(wrapper.text()).toContain('sim_abc')
  })

  it('fetches simulation status on mount', async () => {
    mountChat('sim_xyz')
    await flushPromises()
    expect(axios.get).toHaveBeenCalledWith('/api/simulation/sim_xyz/run-status')
  })

  it('displays simulation status badge', async () => {
    const wrapper = mountChat()
    await flushPromises()
    expect(wrapper.text()).toContain('Running')
  })

  it('does not send empty messages', async () => {
    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('   ')
    await wrapper.find('button').trigger('click')
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('sends user message and displays it', async () => {
    axios.post.mockResolvedValue({
      data: {
        success: true,
        data: { response: 'Hello from MiroFish', tool_calls: [], sources: [] },
      },
    })

    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('What happened in round 5?')
    await input.trigger('keydown.enter')
    await flushPromises()

    expect(wrapper.text()).toContain('What happened in round 5?')
    expect(wrapper.text()).toContain('Hello from MiroFish')
  })

  it('sends correct payload to chat API', async () => {
    axios.post.mockResolvedValue({
      data: { success: true, data: { response: 'Reply', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat('sim_test')
    const input = wrapper.find('input')
    await input.setValue('test question')
    await input.trigger('keydown.enter')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledWith('/api/report/chat', {
      simulation_id: 'sim_test',
      message: 'test question',
      chat_history: [],
    })
  })

  it('displays tool calls as collapsible sections', async () => {
    axios.post.mockResolvedValue({
      data: {
        success: true,
        data: {
          response: 'Analysis complete',
          tool_calls: [
            { name: 'insight_forge', parameters: { query: 'sentiment analysis' } },
            { name: 'panorama_search', parameters: { query: 'round 5 events' } },
          ],
          sources: [],
        },
      },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Analyze sentiment')
    await wrapper.find('input').trigger('keydown.enter')
    await flushPromises()

    expect(wrapper.text()).toContain('Insight Forge')
    expect(wrapper.text()).toContain('Panorama Search')
    expect(wrapper.findAll('details')).toHaveLength(2)
  })

  it('shows error state on API failure', async () => {
    axios.post.mockRejectedValue({
      response: { data: { error: 'Simulation not found' } },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('hello')
    await wrapper.find('input').trigger('keydown.enter')
    await flushPromises()

    expect(wrapper.text()).toContain('Error: Simulation not found')
  })

  it('shows thinking indicator while sending', async () => {
    let resolvePost
    axios.post.mockReturnValue(
      new Promise((resolve) => {
        resolvePost = resolve
      })
    )

    const wrapper = mountChat()
    await wrapper.find('input').setValue('test')
    await wrapper.find('input').trigger('keydown.enter')
    await flushPromises()

    // Should show bouncing dots
    expect(wrapper.findAll('.animate-bounce')).toHaveLength(3)

    resolvePost({
      data: { success: true, data: { response: 'done', tool_calls: [], sources: [] } },
    })
    await flushPromises()

    // Thinking indicator should be gone
    expect(wrapper.findAll('.animate-bounce')).toHaveLength(0)
  })

  it('disables input while sending', async () => {
    let resolvePost
    axios.post.mockReturnValue(
      new Promise((resolve) => {
        resolvePost = resolve
      })
    )

    const wrapper = mountChat()
    await wrapper.find('input').setValue('test')
    await wrapper.find('input').trigger('keydown.enter')
    await flushPromises()

    expect(wrapper.find('input').element.disabled).toBe(true)

    resolvePost({
      data: { success: true, data: { response: 'done', tool_calls: [], sources: [] } },
    })
    await flushPromises()

    expect(wrapper.find('input').element.disabled).toBe(false)
  })

  it('handles API returning success: false', async () => {
    axios.post.mockResolvedValue({
      data: { success: false, error: 'Missing graph ID' },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('query')
    await wrapper.find('input').trigger('keydown.enter')
    await flushPromises()

    expect(wrapper.text()).toContain('Missing graph ID')
  })

  it('clears input after sending', async () => {
    axios.post.mockResolvedValue({
      data: { success: true, data: { response: 'ok', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('hello')
    await input.trigger('keydown.enter')

    expect(input.element.value).toBe('')
  })

  it('shows completed status badge', async () => {
    axios.get.mockResolvedValue({
      data: { success: true, data: { runner_status: 'completed' } },
    })

    const wrapper = mountChat()
    await flushPromises()
    expect(wrapper.text()).toContain('Complete')
  })
})
