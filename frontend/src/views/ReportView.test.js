import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import ReportView from './ReportView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/report/:taskId', component: ReportView, props: true },
      { path: '/chat/:taskId', component: { template: '<div />' } },
      { path: '/', component: { template: '<div />' } },
    ],
  })
}

const MOCK_SECTIONS = [
  {
    filename: 'section_01.md',
    section_index: 1,
    content: '## Executive Summary\n\nThis report analyzes the simulation results.\n\n### Key Findings\n\n- Market sentiment shifted positively after the product launch\n- Competitor response was slower than expected\n- Social media engagement exceeded baseline by 3x',
  },
  {
    filename: 'section_02.md',
    section_index: 2,
    content: '## Market Analysis\n\nDetailed analysis of market conditions.\n\n- Segment A showed 40% growth\n- Segment B remained flat',
  },
  {
    filename: 'section_03.md',
    section_index: 3,
    content: '## Recommendations\n\nBased on the simulation:\n\n- Accelerate go-to-market timeline\n- Focus resources on Segment A',
  },
]

function mockFetchForGenerated() {
  return vi.fn((url, opts) => {
    if (url === '/api/report/generate') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            report_id: 'report_abc123',
            status: 'completed',
            already_generated: true,
          },
        }),
      })
    }
    if (url === '/api/report/report_abc123') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            report_id: 'report_abc123',
            markdown_content: MOCK_SECTIONS.map(s => s.content).join('\n\n'),
          },
        }),
      })
    }
    if (url === '/api/report/report_abc123/sections') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { sections: MOCK_SECTIONS, total_sections: 3, is_complete: true },
        }),
      })
    }
    return Promise.resolve({ ok: false })
  })
}

function mockFetchForGenerating() {
  return vi.fn((url) => {
    if (url === '/api/report/generate') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            report_id: 'report_new456',
            task_id: 'task_789',
            status: 'generating',
            already_generated: false,
          },
        }),
      })
    }
    if (url === '/api/report/report_new456/sections') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { sections: [MOCK_SECTIONS[0]], total_sections: 1, is_complete: false },
        }),
      })
    }
    if (url === '/api/report/report_new456/progress') {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            status: 'generating',
            progress: 33,
            message: 'Generating chapter: Market Analysis',
            completed_sections: ['Executive Summary'],
            current_section: 'Market Analysis',
          },
        }),
      })
    }
    return Promise.resolve({ ok: false })
  })
}

function mockFetchForError() {
  return vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        success: false,
        error: 'Simulation not found',
      }),
    })
  )
}

describe('ReportView', () => {
  let originalFetch

  beforeEach(() => {
    originalFetch = globalThis.fetch
    vi.useFakeTimers()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.useRealTimers()
  })

  it('shows loading state initially', () => {
    globalThis.fetch = vi.fn(() => new Promise(() => {}))
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    expect(wrapper.text()).toContain('Loading report...')
  })

  it('renders header with title and task id', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Simulation Report')
    expect(wrapper.text()).toContain('sim_test')
  })

  it('renders sidebar with summary and chapter titles for completed report', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Summary')
    expect(wrapper.text()).toContain('Executive Summary')
    expect(wrapper.text()).toContain('Market Analysis')
    expect(wrapper.text()).toContain('Recommendations')
  })

  it('shows key findings in summary view by default', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Key Findings')
    expect(wrapper.text()).toContain('Market sentiment shifted positively')
    expect(wrapper.text()).toContain('Competitor response was slower')
  })

  it('displays blue callout boxes for key findings', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    const callouts = wrapper.findAll('.border-\\[\\#2068FF\\]')
    expect(callouts.length).toBeGreaterThan(0)
  })

  it('shows report stats in summary view', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Chapters')
    expect(wrapper.text()).toContain('Key Findings')
    expect(wrapper.text()).toContain('Complete')
  })

  it('renders chapter content when a chapter is clicked', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    const chapterButtons = wrapper.findAll('nav button')
    // Click "Market Analysis" (3rd button: summary, exec summary, market analysis)
    await chapterButtons[2].trigger('click')

    expect(wrapper.find('.report-content').exists()).toBe(true)
    expect(wrapper.text()).toContain('Detailed analysis of market conditions')
  })

  it('shows completion checkmarks for chapters', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    const checkmarks = wrapper.findAll('nav svg path[d="m4.5 12.75 6 6 9-13.5"]')
    expect(checkmarks.length).toBe(3)
  })

  it('shows export button when chapters exist', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Export .md')
  })

  it('exports markdown as a file download', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    const createObjectURL = vi.fn(() => 'blob:test')
    const revokeObjectURL = vi.fn()
    globalThis.URL.createObjectURL = createObjectURL
    globalThis.URL.revokeObjectURL = revokeObjectURL

    const clickSpy = vi.fn()
    vi.spyOn(document, 'createElement').mockReturnValueOnce({
      href: '',
      download: '',
      click: clickSpy,
    })

    const exportBtn = wrapper.findAll('button').find(b => b.text().includes('Export'))
    await exportBtn.trigger('click')

    expect(createObjectURL).toHaveBeenCalled()
    expect(clickSpy).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalled()
  })

  it('shows error state when API fails', async () => {
    globalThis.fetch = mockFetchForError()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Report generation failed')
    expect(wrapper.text()).toContain('Simulation not found')
  })

  it('shows empty state when no report and not generating', async () => {
    globalThis.fetch = vi.fn((url) => {
      if (url === '/api/report/generate') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: { report_id: 'report_empty', status: 'completed', already_generated: true },
          }),
        })
      }
      if (url === '/api/report/report_empty') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: { report_id: 'report_empty', markdown_content: '' },
          }),
        })
      }
      if (url === '/api/report/report_empty/sections') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: { sections: [], total_sections: 0, is_complete: true },
          }),
        })
      }
      return Promise.resolve({ ok: false })
    })
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('No report data yet')
  })

  it('shows progress bar when generating', async () => {
    globalThis.fetch = mockFetchForGenerating()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Executive Summary')
    expect(wrapper.text()).toContain('complete')
  })

  it('renders Ask Follow-Up link to chat', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    const link = wrapper.find('a[href="/chat/sim_test"]')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('Ask Follow-Up')
  })

  it('switches between summary and chapter views', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Key Findings')

    const buttons = wrapper.findAll('nav button')
    await buttons[1].trigger('click')
    expect(wrapper.find('.report-content').exists()).toBe(true)

    await buttons[0].trigger('click')
    expect(wrapper.text()).toContain('Key Findings')
  })

  it('uses TransitionGroup for chapter nav', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    const tg = wrapper.findComponent({ name: 'TransitionGroup' })
    expect(tg.exists()).toBe(true)
  })

  it('uses Transition for chapter content switching', async () => {
    globalThis.fetch = mockFetchForGenerated()
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: { plugins: [router] },
    })
    await flushPromises()

    const buttons = wrapper.findAll('nav button')
    await buttons[1].trigger('click')

    const transition = wrapper.findComponent({ name: 'Transition' })
    expect(transition.exists()).toBe(true)
  })
})
