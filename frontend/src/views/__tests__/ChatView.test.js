import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ChatView from '../ChatView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { taskId: 'sim_123' } }),
}))

vi.mock('../../api/chat', () => ({
  chatApi: {
    send: vi.fn(),
  },
}))

import { chatApi } from '../../api/chat'
import { useSimulationStore } from '../../stores/simulation'

function mountChat(props = {}) {
  return mount(ChatView, {
    props: { taskId: 'sim_123', ...props },
    global: {
      plugins: [createPinia()],
      stubs: {
        StatusIndicator: {
          props: ['status'],
          template: '<span class="status-indicator" :data-status="status"><slot /></span>',
        },
      },
    },
  })
}

describe('ChatView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  it('renders the chat header with title', () => {
    const wrapper = mountChat()
    expect(wrapper.text()).toContain('Chat with Simulation')
  })

  it('shows empty state when no messages exist', () => {
    const wrapper = mountChat()
    expect(wrapper.text()).toContain('Chat with the Simulation')
    expect(wrapper.text()).toContain('Ask follow-up questions')
  })

  it('renders the input field and send button', () => {
    const wrapper = mountChat()
    const input = wrapper.find('input[placeholder="Ask about the simulation results..."]')
    expect(input.exists()).toBe(true)
    const sendButton = wrapper.find('button')
    expect(sendButton.text()).toBe('Send')
  })

  it('disables send button when input is empty', () => {
    const wrapper = mountChat()
    const button = wrapper.findAll('button').find((b) => b.text() === 'Send')
    expect(button.attributes('disabled')).toBeDefined()
  })

  it('enables send button when input has text', async () => {
    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('Hello')
    const button = wrapper.findAll('button').find((b) => b.text() === 'Send')
    expect(button.attributes('disabled')).toBeUndefined()
  })

  it('adds user message to the list on send', async () => {
    chatApi.send.mockResolvedValue({
      data: { success: true, data: { response: 'Hi there', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('Hello world')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')

    expect(wrapper.text()).toContain('Hello world')
  })

  it('clears input after sending', async () => {
    chatApi.send.mockResolvedValue({
      data: { success: true, data: { response: 'Reply', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('Test message')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')

    expect(input.element.value).toBe('')
  })

  it('displays assistant response after API call', async () => {
    chatApi.send.mockResolvedValue({
      data: {
        success: true,
        data: { response: 'The simulation shows positive trends.', tool_calls: [], sources: [] },
      },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('What are the trends?')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('The simulation shows positive trends.')
    expect(wrapper.text()).toContain('MiroFish')
  })

  it('shows error message on API failure', async () => {
    chatApi.send.mockRejectedValue(new Error('Network error'))

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Test')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Network error')
    expect(wrapper.text()).toContain('Error')
  })

  it('shows error when API returns success: false', async () => {
    chatApi.send.mockResolvedValue({
      data: { success: false, error: 'Simulation not found' },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Test')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Simulation not found')
  })

  it('sends correct payload to API', async () => {
    chatApi.send.mockResolvedValue({
      data: { success: true, data: { response: 'Reply', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('My question')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')

    expect(chatApi.send).toHaveBeenCalledWith({
      simulation_id: 'sim_123',
      message: 'My question',
      chat_history: [],
    })
  })

  it('sends chat history on subsequent messages', async () => {
    chatApi.send
      .mockResolvedValueOnce({
        data: { success: true, data: { response: 'First reply', tool_calls: [], sources: [] } },
      })
      .mockResolvedValueOnce({
        data: { success: true, data: { response: 'Second reply', tool_calls: [], sources: [] } },
      })

    const wrapper = mountChat()

    await wrapper.find('input').setValue('First question')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    await wrapper.find('input').setValue('Follow up')
    await wrapper.findAll('button').find((b) => b.text().includes('Send')).trigger('click')

    expect(chatApi.send).toHaveBeenLastCalledWith({
      simulation_id: 'sim_123',
      message: 'Follow up',
      chat_history: [
        { role: 'user', content: 'First question' },
        { role: 'assistant', content: 'First reply' },
      ],
    })
  })

  it('renders tool calls as collapsible details elements', async () => {
    chatApi.send.mockResolvedValue({
      data: {
        success: true,
        data: {
          response: 'Analysis complete.',
          tool_calls: [
            { name: 'insight_forge', arguments: { query: 'trends' }, result: 'Found 5 trends' },
            { name: 'panorama_search', arguments: { term: 'competitors' } },
          ],
          sources: [],
        },
      },
    })

    vi.useFakeTimers()

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Analyze')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    // revealToolCalls uses delay(800) per tool + delay(500) at end
    await vi.advanceTimersByTimeAsync(800)
    await flushPromises()
    await vi.advanceTimersByTimeAsync(800)
    await flushPromises()
    await vi.advanceTimersByTimeAsync(500)
    await flushPromises()

    vi.useRealTimers()

    const details = wrapper.findAll('details')
    expect(details).toHaveLength(2)
    expect(wrapper.text()).toContain('Insight Forge')
    expect(wrapper.text()).toContain('Panorama Search')
  })

  it('renders source badges when sources are returned', async () => {
    chatApi.send.mockResolvedValue({
      data: {
        success: true,
        data: {
          response: 'Here are the results.',
          tool_calls: [],
          sources: ['Knowledge Graph', 'Agent Logs'],
        },
      },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Sources test')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Knowledge Graph')
    expect(wrapper.text()).toContain('Agent Logs')
  })

  it('shows typing indicator while sending', async () => {
    let resolvePromise
    chatApi.send.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      }),
    )

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Slow question')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    const bounceDots = wrapper.findAll('.animate-bounce')
    expect(bounceDots).toHaveLength(3)

    resolvePromise({
      data: { success: true, data: { response: 'Done', tool_calls: [], sources: [] } },
    })
    await flushPromises()

    expect(wrapper.findAll('.animate-bounce')).toHaveLength(0)
  })

  it('shows simulation context indicator', () => {
    const wrapper = mountChat()
    const indicator = wrapper.find('.status-indicator')
    expect(indicator.exists()).toBe(true)
  })

  it('displays simulation ID in context bar', () => {
    const wrapper = mountChat()
    expect(wrapper.text()).toContain('sim_123')
  })

  it('prevents sending while already sending', async () => {
    chatApi.send.mockReturnValue(new Promise(() => {}))

    const wrapper = mountChat()
    await wrapper.find('input').setValue('First')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    const sendButton = wrapper.findAll('button').find((b) => b.text().includes('Send'))
    expect(sendButton.attributes('disabled')).toBeDefined()
  })

  it('sends on Enter keypress', async () => {
    chatApi.send.mockResolvedValue({
      data: { success: true, data: { response: 'Reply', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('Enter test')
    await input.trigger('keydown.enter')
    await flushPromises()

    expect(chatApi.send).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Enter test')
  })

  it('does not send empty messages', async () => {
    const wrapper = mountChat()
    const input = wrapper.find('input')
    await input.setValue('   ')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')

    expect(chatApi.send).not.toHaveBeenCalled()
  })

  it('shows message count in context bar', async () => {
    chatApi.send.mockResolvedValue({
      data: { success: true, data: { response: 'Reply', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Test')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('1 messages')
  })

  it('applies blue background to user messages', async () => {
    chatApi.send.mockResolvedValue({
      data: { success: true, data: { response: 'Reply', tool_calls: [], sources: [] } },
    })

    const wrapper = mountChat()
    await wrapper.find('input').setValue('Blue bubble test')
    await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
    await flushPromises()

    const userBubble = wrapper.find('.bg-\\[\\#2068FF\\]')
    expect(userBubble.exists()).toBe(true)
    expect(userBubble.text()).toContain('Blue bubble test')
  })
})
