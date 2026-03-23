import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import ReportView from './ReportView.vue'

vi.mock('../services/api.js', () => ({
  generateReport: vi.fn().mockResolvedValue({
    data: { report_id: 'rpt-1', task_id: 'task-1', already_generated: true },
  }),
  getReportGenerateStatus: vi.fn(),
  getReportSections: vi.fn().mockResolvedValue({
    data: {
      sections: [
        { content: '# Executive Summary\nThis is the executive summary.' },
        { content: '## Key Findings\nHere are the key findings.' },
      ],
    },
  }),
  pollTask: vi.fn(),
}))

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/report/:taskId', component: ReportView, props: true },
      { path: '/chat/:taskId', component: { template: '<div />' } },
    ],
  })
}

describe('ReportView', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  async function mountView() {
    const router = createTestRouter()
    await router.push('/report/sim-1?simulationId=sim-1')
    await router.isReady()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim-1' },
      global: { plugins: [router] },
    })
    await flushPromises()
    return wrapper
  }

  it('renders chapter nav buttons from sections', async () => {
    const wrapper = await mountView()
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBeGreaterThanOrEqual(2)
    expect(buttons[0].text()).toBe('Executive Summary')
    expect(buttons[1].text()).toBe('Key Findings')
  })

  it('shows first chapter content by default', async () => {
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('This is the executive summary.')
  })

  it('switches chapter content on nav click', async () => {
    const wrapper = await mountView()
    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Here are the key findings.')
  })

  it('uses Transition for chapter switching', async () => {
    const wrapper = await mountView()
    // Vue Transition component renders in the DOM
    const transition = wrapper.findComponent({ name: 'Transition' })
    expect(transition.exists()).toBe(true)
  })

  it('uses TransitionGroup for chapter nav', async () => {
    const wrapper = await mountView()
    const tg = wrapper.findComponent({ name: 'TransitionGroup' })
    expect(tg.exists()).toBe(true)
  })
})
