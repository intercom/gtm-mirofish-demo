import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LiveFeed from '../LiveFeed.vue'

function makeAction(overrides = {}) {
  return {
    round_num: 5,
    agent_id: 1,
    agent_name: 'VP Sales, Strategy @ Intercom',
    platform: 'twitter',
    action_type: 'CREATE_POST',
    action_args: { content: 'Great strategy update' },
    ...overrides,
  }
}

function mountFeed(props = {}) {
  return mount(LiveFeed, {
    props: {
      actions: [],
      ...props,
    },
  })
}

describe('LiveFeed', () => {
  it('shows "Live Feed" heading', () => {
    const wrapper = mountFeed()
    expect(wrapper.text()).toContain('Live Feed')
  })

  it('shows empty state when no actions', () => {
    const wrapper = mountFeed({ actions: [] })
    expect(wrapper.text()).toContain('Waiting for agent activity...')
  })

  it('shows empty state description text', () => {
    const wrapper = mountFeed({ actions: [] })
    expect(wrapper.text()).toContain('Posts, replies, likes, and reposts will stream here in real-time')
  })

  it('renders agent short name (first part before comma)', () => {
    const wrapper = mountFeed({ actions: [makeAction()] })
    expect(wrapper.text()).toContain('VP Sales')
  })

  it('shows action label "Posted" for CREATE_POST', () => {
    const wrapper = mountFeed({ actions: [makeAction({ action_type: 'CREATE_POST' })] })
    expect(wrapper.text()).toContain('Posted')
  })

  it('shows action label "Replied" for REPLY_POST', () => {
    const wrapper = mountFeed({ actions: [makeAction({ action_type: 'REPLY_POST' })] })
    expect(wrapper.text()).toContain('Replied')
  })

  it('shows action label "Liked" for LIKE', () => {
    const wrapper = mountFeed({ actions: [makeAction({ action_type: 'LIKE' })] })
    expect(wrapper.text()).toContain('Liked')
  })

  it('shows action label "Reposted" for REPOST', () => {
    const wrapper = mountFeed({ actions: [makeAction({ action_type: 'REPOST' })] })
    expect(wrapper.text()).toContain('Reposted')
  })

  it('shows platform badge "X" for twitter', () => {
    const wrapper = mountFeed({ actions: [makeAction({ platform: 'twitter' })] })
    const badges = wrapper.findAll('span').filter(s => s.text() === 'X')
    expect(badges.length).toBeGreaterThan(0)
  })

  it('shows platform badge "Reddit" for reddit', () => {
    const wrapper = mountFeed({ actions: [makeAction({ platform: 'reddit' })] })
    const badges = wrapper.findAll('span').filter(s => s.text() === 'Reddit')
    expect(badges.length).toBeGreaterThan(0)
  })

  it('shows round number "R5" badge', () => {
    const wrapper = mountFeed({ actions: [makeAction({ round_num: 5 })] })
    expect(wrapper.text()).toContain('R5')
  })

  it('shows action content text', () => {
    const wrapper = mountFeed({ actions: [makeAction()] })
    expect(wrapper.text()).toContain('Great strategy update')
  })

  it('truncates long content to 140 chars', () => {
    const longContent = 'A'.repeat(200)
    const wrapper = mountFeed({
      actions: [makeAction({ action_args: { content: longContent } })],
    })
    expect(wrapper.text()).toContain('A'.repeat(140) + '\u2026')
    expect(wrapper.text()).not.toContain('A'.repeat(141))
  })

  it('shows event count', () => {
    const actions = [makeAction(), makeAction({ agent_id: 2 })]
    const wrapper = mountFeed({ actions })
    expect(wrapper.text()).toContain('2 events')
  })

  it('filters actions by twitter platform on tab click', async () => {
    const actions = [
      makeAction({ platform: 'twitter', agent_name: 'Agent Twitter' }),
      makeAction({ platform: 'reddit', agent_name: 'Agent Reddit', agent_id: 2 }),
    ]
    const wrapper = mountFeed({ actions })
    const twitterBtn = wrapper.findAll('button').find(b => b.text() === 'Twitter')
    await twitterBtn.trigger('click')
    expect(wrapper.text()).toContain('Agent Twitter')
    expect(wrapper.text()).not.toContain('Agent Reddit')
  })

  it('filters actions by reddit platform on tab click', async () => {
    const actions = [
      makeAction({ platform: 'twitter', agent_name: 'Agent Twitter' }),
      makeAction({ platform: 'reddit', agent_name: 'Agent Reddit', agent_id: 2 }),
    ]
    const wrapper = mountFeed({ actions })
    const redditBtn = wrapper.findAll('button').find(b => b.text() === 'Reddit')
    await redditBtn.trigger('click')
    expect(wrapper.text()).toContain('Agent Reddit')
    expect(wrapper.text()).not.toContain('Agent Twitter')
  })

  it('filters actions by type (posts)', async () => {
    const actions = [
      makeAction({ action_type: 'CREATE_POST', agent_name: 'Poster' }),
      makeAction({ action_type: 'LIKE', agent_name: 'Liker', agent_id: 2 }),
    ]
    const wrapper = mountFeed({ actions })
    const select = wrapper.find('select')
    await select.setValue('post')
    expect(wrapper.text()).toContain('Poster')
    expect(wrapper.text()).not.toContain('Liker')
  })

  it('filters by search query matching agent name', async () => {
    const actions = [
      makeAction({ agent_name: 'VP Sales, Strategy' }),
      makeAction({ agent_name: 'CTO, Engineering', agent_id: 2 }),
    ]
    const wrapper = mountFeed({ actions })
    const input = wrapper.find('input[type="text"]')
    await input.setValue('VP Sales')
    expect(wrapper.text()).toContain('VP Sales')
    expect(wrapper.text()).not.toContain('CTO')
  })

  it('filters by search query matching content', async () => {
    const actions = [
      makeAction({ action_args: { content: 'Alpha launch' } }),
      makeAction({ action_args: { content: 'Beta release' }, agent_id: 2 }),
    ]
    const wrapper = mountFeed({ actions })
    const input = wrapper.find('input[type="text"]')
    await input.setValue('Alpha')
    expect(wrapper.text()).toContain('Alpha launch')
    expect(wrapper.text()).not.toContain('Beta release')
  })

  it('shows connection status "Polling" by default', () => {
    const wrapper = mountFeed()
    expect(wrapper.text()).toContain('Polling')
  })

  it('shows connection status "Live" for connected', () => {
    const wrapper = mountFeed({ connectionStatus: 'connected' })
    expect(wrapper.text()).toContain('Live')
  })

  it('shows thinking toggle button', () => {
    const wrapper = mountFeed()
    expect(wrapper.text()).toContain('Show Thinking')
  })

  it('emits toggle-thinking on button click', async () => {
    const wrapper = mountFeed()
    const btn = wrapper.findAll('button').find(b => b.text().includes('Show Thinking'))
    await btn.trigger('click')
    expect(wrapper.emitted('toggle-thinking')).toHaveLength(1)
  })

  it('emits select-agent when agent name is clicked', async () => {
    const action = makeAction()
    const wrapper = mountFeed({ actions: [action] })
    const agentBtn = wrapper.findAll('button').find(b => b.text().includes('VP Sales'))
    await agentBtn.trigger('click')
    expect(wrapper.emitted('select-agent')).toHaveLength(1)
    expect(wrapper.emitted('select-agent')[0][0]).toEqual(action)
  })

  it('shows LLM model badge when showThinking and llmModel are set', () => {
    const wrapper = mountFeed({ showThinking: true, llmModel: 'claude-3-opus', llmProvider: 'Anthropic' })
    expect(wrapper.text()).toContain('claude-3-opus')
    expect(wrapper.text()).toContain('Anthropic')
  })
})
