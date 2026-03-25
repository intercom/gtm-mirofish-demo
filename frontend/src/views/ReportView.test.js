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
      { path: '/workspace/:taskId', component: { template: '<div />' } },
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
  return vi.fn((url) => {
    if (url.includes('/report/check/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: {
            has_report: true,
            report_id: 'report_abc123',
            report_status: 'completed',
          },
        }),
      })
    }
    if (url.includes('/report/report_abc123/sections')) {
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
    if (url.includes('/report/check/')) {
      return Promise.resolve({ ok: false })
    }
    if (url.includes('/report/generate')) {
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
    if (url.includes('/report/report_new456/sections')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { sections: [MOCK_SECTIONS[0]], total_sections: 1, is_complete: false },
        }),
      })
    }
    if (url.includes('/report/report_new456/progress')) {
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
  return vi.fn((url) => {
    if (url.includes('/report/check/')) {
      return Promise.resolve({ ok: false })
    }
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        success: false,
        error: 'Simulation not found',
      }),
    })
  })
}

function mountReport(fetchMock, opts = {}) {
  globalThis.fetch = fetchMock
  const router = createTestRouter()
  return mount(ReportView, {
    props: { taskId: 'sim_test' },
    global: {
      plugins: [router],
      stubs: {
        PhaseNav: { props: ['taskId', 'activePhase'], template: '<div class="phase-nav"></div>' },
        ShimmerCard: { template: '<div class="shimmer"></div>' },
        ReportCharts: { props: ['chapterIndex'], template: '<div class="charts"></div>' },
      },
    },
    ...opts,
  })
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

  it('shows shimmer loading state while generating with no content', async () => {
    globalThis.fetch = vi.fn(() => new Promise(() => {}))
    const router = createTestRouter()
    const wrapper = mount(ReportView, {
      props: { taskId: 'sim_test' },
      global: {
        plugins: [router],
        stubs: {
          PhaseNav: { props: ['taskId', 'activePhase'], template: '<div class="phase-nav"></div>' },
          ShimmerCard: { template: '<div class="shimmer"></div>' },
          ReportCharts: { props: ['chapterIndex'], template: '<div class="charts"></div>' },
        },
      },
    })
    expect(wrapper.text()).toContain('Predictive Report')
  })

  it('renders header with title', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    expect(wrapper.text()).toContain('Predictive Report')
  })

  it('renders sidebar with chapter titles for completed report', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    expect(wrapper.text()).toContain('Executive Summary')
    expect(wrapper.text()).toContain('Market Analysis')
    expect(wrapper.text()).toContain('Recommendations')
  })

  it('shows key findings extracted from chapters', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    expect(wrapper.text()).toContain('Key Findings')
    expect(wrapper.text()).toContain('Market sentiment shifted positively')
    expect(wrapper.text()).toContain('Competitor response was slower')
  })

  it('renders chapter content when a chapter is clicked', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    const chapterButtons = wrapper.findAll('nav button')
    const marketAnalysisBtn = chapterButtons.find(b => b.text().includes('Market Analysis'))
    await marketAnalysisBtn.trigger('click')

    expect(wrapper.find('.report-content').exists()).toBe(true)
    expect(wrapper.text()).toContain('Detailed analysis of market conditions')
  })

  it('shows completion checkmarks for chapters', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    const checkmarks = wrapper.findAll('nav svg path[d="M5 13l4 4L19 7"]')
    expect(checkmarks.length).toBe(3)
  })

  it('shows export button when chapters exist and report is complete', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    expect(wrapper.text()).toContain('Export Markdown')
  })

  it('exports markdown via window.open', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    const exportBtn = wrapper.findAll('button').find(b => b.text().includes('Export'))
    await exportBtn.trigger('click')

    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining('/report/report_abc123/download'),
      '_blank',
    )
    openSpy.mockRestore()
  })

  it('shows error state when generation API fails', async () => {
    const wrapper = mountReport(mockFetchForError())
    await flushPromises()

    expect(wrapper.text()).toContain('Simulation not found')
  })

  it('shows empty state when no sections and not generating', async () => {
    globalThis.fetch = vi.fn((url) => {
      if (url.includes('/report/check/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            data: { has_report: true, report_id: 'report_empty', report_status: 'completed' },
          }),
        })
      }
      if (url.includes('/report/report_empty/sections')) {
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
      global: {
        plugins: [router],
        stubs: {
          PhaseNav: { props: ['taskId', 'activePhase'], template: '<div class="phase-nav"></div>' },
          ShimmerCard: { template: '<div class="shimmer"></div>' },
          ReportCharts: { props: ['chapterIndex'], template: '<div class="charts"></div>' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('No report content available')
  })

  it('shows progress bar when generating', async () => {
    const wrapper = mountReport(mockFetchForGenerating())
    await flushPromises()

    // Trigger the poll interval to execute
    await vi.advanceTimersByTimeAsync(3000)
    await flushPromises()

    expect(wrapper.text()).toContain('Executive Summary')
    expect(wrapper.text()).toContain('33%')
  })

  it('renders Ask Follow-Up link to chat', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    const link = wrapper.find('a')
    expect(link.text()).toContain('Ask Follow-Up')
  })

  it('displays chapter navigation footer when multiple chapters exist', async () => {
    const wrapper = mountReport(mockFetchForGenerated())
    await flushPromises()

    expect(wrapper.text()).toContain('Previous Chapter')
    expect(wrapper.text()).toContain('Next Chapter')
    expect(wrapper.text()).toContain('1 of 3')
  })
})
