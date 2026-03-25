import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AgentProfileView from '../AgentProfileView.vue'

const AGENT_VP = 'Sarah Chen, VP of Sales@Acme Corp'
const AGENT_ENGINEER = 'Alex Rivera, IT Engineer@TechCo'
const AGENT_OPS = 'Jordan Lee, Operations Manager@Globex'
const AGENT_GENERIC = 'Pat Kim, Product Lead@StartupHQ'

let mockRoute = {
  params: { taskId: 'sim_abc', agentId: 'agent-42' },
  query: { name: AGENT_VP },
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
}))

vi.mock('../../api/client', () => ({
  default: {
    post: vi.fn(),
  },
}))

import client from '../../api/client'

function mountAgent(props = {}, query = {}) {
  if (Object.keys(query).length) {
    mockRoute = {
      ...mockRoute,
      query: { ...mockRoute.query, ...query },
    }
  }
  return mount(AgentProfileView, {
    props: {
      taskId: 'sim_abc',
      agentId: 'agent-42',
      ...props,
    },
    global: {
      plugins: [createPinia()],
      stubs: {
        'router-link': {
          props: ['to'],
          template: '<a :href="to" class="router-link-stub"><slot /></a>',
        },
      },
    },
  })
}

describe('AgentProfileView — E2E agent management', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    mockRoute = {
      params: { taskId: 'sim_abc', agentId: 'agent-42' },
      query: { name: AGENT_VP },
    }
  })

  // ── Name / role / company parsing ──────────────────────────

  describe('agent identity parsing', () => {
    it('parses name, role, and company from VP agent', () => {
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Sarah Chen')
      expect(wrapper.text()).toContain('VP of Sales')
      expect(wrapper.text()).toContain('@ Acme Corp')
    })

    it('parses engineer agent identity', () => {
      mockRoute.query.name = AGENT_ENGINEER
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Alex Rivera')
      expect(wrapper.text()).toContain('IT Engineer')
      expect(wrapper.text()).toContain('@ TechCo')
    })

    it('shows avatar initial from first character of name', () => {
      const wrapper = mountAgent()
      const avatar = wrapper.find('.rounded-full.bg-\\[var\\(--color-primary\\)\\]')
      expect(avatar.text()).toBe('S')
    })

    it('falls back to "Agent {id}" when no name in query', () => {
      mockRoute.query = {}
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Agent agent-42')
    })
  })

  // ── Sentiment badges ───────────────────────────────────────

  describe('sentiment labels by role', () => {
    it('shows "Positive" for VP/Director roles', () => {
      mockRoute.query.name = AGENT_VP
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Positive')
    })

    it('shows "Skeptical" for IT/Engineer roles', () => {
      mockRoute.query.name = AGENT_ENGINEER
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Skeptical')
    })

    it('shows "Cautious" for Ops roles', () => {
      mockRoute.query.name = AGENT_OPS
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Cautious')
    })

    it('shows "Neutral-Positive" for generic roles', () => {
      mockRoute.query.name = AGENT_GENERIC
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Neutral-Positive')
    })
  })

  // ── Overview tab (default) ─────────────────────────────────

  describe('overview tab', () => {
    it('is active by default', () => {
      const wrapper = mountAgent()
      const buttons = wrapper.findAll('button')
      const overviewBtn = buttons.find((b) => b.text() === 'Overview')
      expect(overviewBtn.classes()).toContain('text-[var(--color-primary)]')
    })

    it('shows stats grid with total, twitter, reddit counts', () => {
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Total Actions')
      expect(wrapper.text()).toContain('Twitter')
      expect(wrapper.text()).toContain('Reddit')
    })

    it('shows VP persona priorities', () => {
      mockRoute.query.name = AGENT_VP
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('ROI and cost efficiency')
      expect(wrapper.text()).toContain('Team productivity')
      expect(wrapper.text()).toContain('Vendor consolidation')
    })

    it('shows VP persona objections', () => {
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Migration risk and downtime')
      expect(wrapper.text()).toContain('Contract lock-in concerns')
    })

    it('shows VP communication style', () => {
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Executive')
      expect(wrapper.text()).toContain('data-driven')
    })

    it('shows VP decision factors', () => {
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('TCO comparison')
      expect(wrapper.text()).toContain('Peer references')
      expect(wrapper.text()).toContain('Pilot program availability')
    })

    it('shows engineer persona traits for IT role', () => {
      mockRoute.query.name = AGENT_ENGINEER
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Security and compliance')
      expect(wrapper.text()).toContain('API quality and documentation')
      expect(wrapper.text()).toContain('Data migration complexity')
      expect(wrapper.text()).toContain('Technical')
    })

    it('shows ops persona traits for Operations role', () => {
      mockRoute.query.name = AGENT_OPS
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Process efficiency')
      expect(wrapper.text()).toContain('Change management overhead')
      expect(wrapper.text()).toContain('Process-oriented')
    })

    it('shows generic persona traits for unrecognized role', () => {
      mockRoute.query.name = AGENT_GENERIC
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Customer satisfaction')
      expect(wrapper.text()).toContain('Learning curve')
      expect(wrapper.text()).toContain('Balanced')
    })

    it('displays section headings for persona cards', () => {
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('Priorities')
      expect(wrapper.text()).toContain('Likely Objections')
      expect(wrapper.text()).toContain('Communication Style')
      expect(wrapper.text()).toContain('Decision Factors')
    })
  })

  // ── Tab switching ──────────────────────────────────────────

  describe('tab navigation', () => {
    it('renders all three tab buttons', () => {
      const wrapper = mountAgent()
      const tabLabels = wrapper
        .findAll('button')
        .map((b) => b.text())
        .filter((t) => ['Overview', 'Activity', 'Interview'].includes(t))
      expect(tabLabels).toEqual(['Overview', 'Activity', 'Interview'])
    })

    it('switches to Activity tab on click', async () => {
      const wrapper = mountAgent()
      const activityTab = wrapper.findAll('button').find((b) => b.text() === 'Activity')
      await activityTab.trigger('click')

      expect(wrapper.text()).not.toContain('Priorities')
      expect(wrapper.text()).toContain('on twitter')
    })

    it('switches to Interview tab on click', async () => {
      const wrapper = mountAgent()
      const interviewTab = wrapper.findAll('button').find((b) => b.text() === 'Interview')
      await interviewTab.trigger('click')

      const input = wrapper.find('input[placeholder="Ask this agent anything..."]')
      expect(input.exists()).toBe(true)
      expect(wrapper.text()).toContain('Send')
    })

    it('switches back to Overview from Activity', async () => {
      const wrapper = mountAgent()
      const activityTab = wrapper.findAll('button').find((b) => b.text() === 'Activity')
      await activityTab.trigger('click')

      const overviewTab = wrapper.findAll('button').find((b) => b.text() === 'Overview')
      await overviewTab.trigger('click')

      expect(wrapper.text()).toContain('Priorities')
    })
  })

  // ── Activity tab ───────────────────────────────────────────

  describe('activity tab', () => {
    async function mountWithActivity() {
      const wrapper = mountAgent()
      const activityTab = wrapper.findAll('button').find((b) => b.text() === 'Activity')
      await activityTab.trigger('click')
      return wrapper
    }

    it('displays action items with platform labels', async () => {
      const wrapper = await mountWithActivity()
      const hasTwitter = wrapper.text().includes('on twitter')
      const hasReddit = wrapper.text().includes('on reddit')
      expect(hasTwitter || hasReddit).toBe(true)
    })

    it('shows round timestamps', async () => {
      const wrapper = await mountWithActivity()
      expect(wrapper.text()).toMatch(/Round \d+, Hour \d+/)
    })

    it('shows action type descriptions', async () => {
      const wrapper = await mountWithActivity()
      const actionTypes = [
        'Viewed sponsored post',
        'Liked tweet',
        'Retweeted content',
        'Replied to thread',
        'Clicked CTA link',
        'Shared with team',
        'Commented on post',
        'Bookmarked article',
        'Upvoted discussion',
        'Asked follow-up question',
        'Downloaded whitepaper',
        'Mentioned competitor',
        'Quoted ROI stat',
        'Engaged with case study',
        'Dismissed ad',
      ]
      const hasAnyAction = actionTypes.some((a) => wrapper.text().includes(a))
      expect(hasAnyAction).toBe(true)
    })
  })

  // ── Interview tab ──────────────────────────────────────────

  describe('interview tab', () => {
    async function mountWithInterview() {
      const wrapper = mountAgent()
      const interviewTab = wrapper.findAll('button').find((b) => b.text() === 'Interview')
      await interviewTab.trigger('click')
      return wrapper
    }

    it('shows initial greeting from agent', async () => {
      const wrapper = await mountWithInterview()
      expect(wrapper.text()).toContain("I'm Sarah Chen")
      expect(wrapper.text()).toContain('VP of Sales')
      expect(wrapper.text()).toContain('Acme Corp')
    })

    it('disables send button when input is empty', async () => {
      const wrapper = await mountWithInterview()
      const sendBtn = wrapper.findAll('button').find((b) => b.text() === 'Send')
      expect(sendBtn.attributes('disabled')).toBeDefined()
    })

    it('enables send button when input has text', async () => {
      const wrapper = await mountWithInterview()
      const input = wrapper.find('input[placeholder="Ask this agent anything..."]')
      await input.setValue('What resonated with you?')
      const sendBtn = wrapper.findAll('button').find((b) => b.text() === 'Send')
      expect(sendBtn.attributes('disabled')).toBeUndefined()
    })

    it('sends user message and displays it', async () => {
      client.post.mockResolvedValue({
        data: { success: true, data: { response: 'The ROI data was compelling.' } },
      })

      const wrapper = await mountWithInterview()
      const input = wrapper.find('input')
      await input.setValue('What messaging worked?')
      const sendBtn = wrapper.findAll('button').find((b) => b.text() === 'Send')
      await sendBtn.trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('What messaging worked?')
      expect(wrapper.text()).toContain('The ROI data was compelling.')
    })

    it('clears input after sending', async () => {
      client.post.mockResolvedValue({
        data: { success: true, data: { response: 'Great question.' } },
      })

      const wrapper = await mountWithInterview()
      const input = wrapper.find('input')
      await input.setValue('Tell me more')
      await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')

      expect(input.element.value).toBe('')
    })

    it('sends correct payload to interview API', async () => {
      client.post.mockResolvedValue({
        data: { success: true, data: { response: 'Reply' } },
      })

      const wrapper = await mountWithInterview()
      await wrapper.find('input').setValue('What would make you switch?')
      await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')

      expect(client.post).toHaveBeenCalledWith('/simulation/interview', {
        agent_name: 'Sarah Chen',
        agent_role: 'VP of Sales',
        agent_company: 'Acme Corp',
        prompt: 'What would make you switch?',
        chat_history: expect.any(Array),
      })
    })

    it('falls back to canned response on API error (demo mode)', async () => {
      client.post.mockRejectedValue(new Error('Network error'))

      const wrapper = await mountWithInterview()
      await wrapper.find('input').setValue('Your thoughts?')
      await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('Your thoughts?')
      expect(wrapper.text()).toContain('cost efficiency')
      expect(wrapper.text()).toContain('pilot program')
    })

    it('shows typing indicator while sending', async () => {
      let resolvePromise
      client.post.mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve
        }),
      )

      const wrapper = await mountWithInterview()
      await wrapper.find('input').setValue('Slow question')
      await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
      await flushPromises()

      const bounceDots = wrapper.findAll('.animate-bounce')
      expect(bounceDots).toHaveLength(3)

      resolvePromise({ data: { data: { response: 'Done' } } })
      await flushPromises()

      expect(wrapper.findAll('.animate-bounce')).toHaveLength(0)
    })

    it('prevents double-sending while request is in flight', async () => {
      client.post.mockReturnValue(new Promise(() => {}))

      const wrapper = await mountWithInterview()
      await wrapper.find('input').setValue('First')
      await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
      await flushPromises()

      const sendBtn = wrapper.findAll('button').find((b) => b.text().includes('Send'))
      expect(sendBtn.attributes('disabled')).toBeDefined()
    })

    it('sends on Enter keypress', async () => {
      client.post.mockResolvedValue({
        data: { data: { response: 'Enter reply' } },
      })

      const wrapper = await mountWithInterview()
      const input = wrapper.find('input')
      await input.setValue('Enter test')
      await input.trigger('keydown.enter')
      await flushPromises()

      expect(client.post).toHaveBeenCalled()
      expect(wrapper.text()).toContain('Enter test')
    })

    it('does not send empty or whitespace-only messages', async () => {
      const wrapper = await mountWithInterview()
      await wrapper.find('input').setValue('   ')
      await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')

      expect(client.post).not.toHaveBeenCalled()
    })

    it('accumulates chat history across multiple exchanges', async () => {
      client.post
        .mockResolvedValueOnce({
          data: { data: { response: 'First reply' } },
        })
        .mockResolvedValueOnce({
          data: { data: { response: 'Second reply' } },
        })

      const wrapper = await mountWithInterview()

      await wrapper.find('input').setValue('Question 1')
      await wrapper.findAll('button').find((b) => b.text() === 'Send').trigger('click')
      await flushPromises()

      await wrapper.find('input').setValue('Question 2')
      await wrapper.findAll('button').find((b) => b.text().includes('Send')).trigger('click')
      await flushPromises()

      expect(wrapper.text()).toContain('First reply')
      expect(wrapper.text()).toContain('Second reply')
    })
  })

  // ── Navigation ─────────────────────────────────────────────

  describe('navigation', () => {
    it('renders back link to simulation workspace', () => {
      const wrapper = mountAgent()
      const backLink = wrapper.find('.router-link-stub')
      expect(backLink.exists()).toBe(true)
      expect(backLink.attributes('href')).toBe('/workspace/sim_abc?tab=simulation')
      expect(backLink.text()).toContain('Back to Simulation')
    })
  })

  // ── Stats determinism ──────────────────────────────────────

  describe('stats consistency', () => {
    it('produces consistent stats for the same agent name', () => {
      const wrapper1 = mountAgent()
      const wrapper2 = mountAgent()
      expect(wrapper1.text()).toEqual(wrapper2.text())
    })

    it('shows platform count label', () => {
      const wrapper = mountAgent()
      expect(wrapper.text()).toContain('2 platforms')
    })
  })
})
