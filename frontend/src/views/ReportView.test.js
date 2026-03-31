import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import ReportView from './ReportView.vue'

// === E2E lifecycle test helpers ===

const mockRouterLink = {
  template: '<a :href="to"><slot /></a>',
  props: ['to'],
}

function okJson(data) {
  return { ok: true, json: async () => data }
}

function mountReportE2E(fetchFn) {
  global.fetch = fetchFn
  return mount(ReportView, {
    props: { taskId: 'sim_e2e' },
    global: {
      stubs: { 'router-link': mockRouterLink },
    },
  })
}

// === Component rendering test helpers ===

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

// === E2E lifecycle tests ===

describe('ReportView — report generation flow (E2E)', () => {
  let originalFetch

  beforeEach(() => {
    originalFetch = global.fetch
    vi.useFakeTimers()
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.useRealTimers()
  })

  describe('full generation lifecycle', () => {
    it('check → 404 → generate → poll with progress → sections arrive → complete', async () => {
      let pollCount = 0

      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return { ok: false, status: 404, json: async () => ({ success: false }) }
        }

        if (url.includes('/report/generate')) {
          return okJson({
            success: true,
            data: {
              report_id: 'rpt_001',
              task_id: 'task_001',
              status: 'generating',
              already_generated: false,
            },
          })
        }

        if (url.includes('/report/rpt_001/progress')) {
          pollCount++
          if (pollCount === 1) {
            return okJson({ success: true, data: { progress: 30, message: 'Generating: Executive Summary' } })
          }
          if (pollCount === 2) {
            return okJson({ success: true, data: { progress: 65, message: 'Generating: Market Analysis' } })
          }
          return okJson({ success: true, data: { progress: 100, message: 'Report complete' } })
        }

        if (url.includes('/report/rpt_001/sections')) {
          if (pollCount <= 1) {
            return okJson({
              success: true,
              data: {
                sections: [
                  { filename: 'section_01.md', section_index: 1, content: '## Executive Summary\n\nFirst section.' },
                ],
                total_sections: 1,
                is_complete: false,
              },
            })
          }
          if (pollCount === 2) {
            return okJson({
              success: true,
              data: {
                sections: [
                  { filename: 'section_01.md', section_index: 1, content: '## Executive Summary\n\nFirst section.' },
                  { filename: 'section_02.md', section_index: 2, content: '## Market Analysis\n\nSecond section.' },
                ],
                total_sections: 2,
                is_complete: false,
              },
            })
          }
          return okJson({
            success: true,
            data: {
              sections: [
                { filename: 'section_01.md', section_index: 1, content: '## Executive Summary\n\nFirst section.' },
                { filename: 'section_02.md', section_index: 2, content: '## Market Analysis\n\nSecond section.' },
                { filename: 'section_03.md', section_index: 3, content: '## Recommendations\n\nThird section.' },
              ],
              total_sections: 3,
              is_complete: true,
            },
          })
        }

        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)

      await flushPromises()
      await flushPromises()

      expect(wrapper.findAll('nav button').length).toBe(1)
      expect(wrapper.text()).toContain('Executive Summary')
      expect(wrapper.text()).toContain('Generating next...')

      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      expect(wrapper.findAll('nav button').length).toBe(2)
      expect(wrapper.text()).toContain('Market Analysis')

      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      expect(wrapper.findAll('nav button').length).toBe(3)
      expect(wrapper.text()).toContain('Recommendations')
      expect(wrapper.text()).not.toContain('Generating next...')

      const callCountAtComplete = fetchFn.mock.calls.length
      await vi.advanceTimersByTimeAsync(6000)
      expect(fetchFn.mock.calls.length).toBe(callCountAtComplete)
    })

    it('shows progress bar with percentage during generation', async () => {
      let pollDone = false
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return { ok: false, status: 404, json: async () => ({ success: false }) }
        }
        if (url.includes('/report/generate')) {
          return okJson({
            success: true,
            data: { report_id: 'rpt_p', task_id: 'task_p', status: 'generating', already_generated: false },
          })
        }
        if (url.includes('/progress')) {
          return okJson({
            success: true,
            data: { progress: pollDone ? 100 : 45, message: 'Generating...' },
          })
        }
        if (url.includes('/sections')) {
          return okJson({
            success: true,
            data: {
              sections: [{ filename: 's1.md', section_index: 1, content: '## Chapter 1\n\nContent.' }],
              total_sections: 1,
              is_complete: pollDone,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()
      await flushPromises()

      expect(wrapper.text()).toContain('45%')
      const progressBar = wrapper.find('[style*="width"]')
      expect(progressBar.exists()).toBe(true)

      pollDone = true
      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      expect(wrapper.text()).not.toContain('45%')
    })
  })

  describe('cache hit — already-generated report', () => {
    it('skips polling when generate returns already_generated: true', async () => {
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return { ok: false, status: 404, json: async () => ({ success: false }) }
        }
        if (url.includes('/report/generate')) {
          return okJson({
            success: true,
            data: { report_id: 'rpt_cached', status: 'completed', already_generated: true },
          })
        }
        if (url.includes('/sections')) {
          return okJson({
            success: true,
            data: {
              sections: [
                { filename: 's1.md', section_index: 1, content: '## Cached Report\n\nCached content.' },
              ],
              total_sections: 1,
              is_complete: true,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()

      expect(wrapper.text()).toContain('Cached Report')
      expect(wrapper.text()).not.toContain('Generating next...')

      const progressCalls = fetchFn.mock.calls.filter(([url]) => url.includes('/progress'))
      expect(progressCalls.length).toBe(0)
    })
  })

  describe('pre-completed report via check endpoint', () => {
    it('loads report directly when check returns completed status', async () => {
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return okJson({
            success: true,
            data: { has_report: true, report_id: 'rpt_existing', report_status: 'completed' },
          })
        }
        if (url.includes('/sections')) {
          return okJson({
            success: true,
            data: {
              sections: [
                { filename: 's1.md', section_index: 1, content: '## Existing Report\n\nAlready done.' },
                { filename: 's2.md', section_index: 2, content: '## Details\n\nMore content.' },
              ],
              total_sections: 2,
              is_complete: true,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()

      expect(wrapper.findAll('nav button').length).toBe(2)
      expect(wrapper.text()).toContain('Existing Report')
      expect(wrapper.text()).not.toContain('Generating')

      const generateCalls = fetchFn.mock.calls.filter(([url]) => url.includes('/report/generate'))
      const progressCalls = fetchFn.mock.calls.filter(([url]) => url.includes('/progress'))
      expect(generateCalls.length).toBe(0)
      expect(progressCalls.length).toBe(0)
    })

    it('resumes polling when check returns generating status', async () => {
      let pollCount = 0
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return okJson({
            success: true,
            data: { has_report: true, report_id: 'rpt_inprogress', report_status: 'generating' },
          })
        }
        if (url.includes('/progress')) {
          pollCount++
          return okJson({
            success: true,
            data: { progress: pollCount >= 2 ? 100 : 50, message: 'Working...' },
          })
        }
        if (url.includes('/sections')) {
          return okJson({
            success: true,
            data: {
              sections: [{ filename: 's1.md', section_index: 1, content: '## In Progress\n\nContent.' }],
              total_sections: 1,
              is_complete: pollCount >= 2,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()
      await flushPromises()

      expect(wrapper.text()).toContain('Generating next...')

      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      expect(wrapper.text()).not.toContain('Generating next...')
    })
  })

  describe('error handling', () => {
    it('shows error when generate endpoint returns failure', async () => {
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return { ok: false, status: 404, json: async () => ({ success: false }) }
        }
        if (url.includes('/report/generate')) {
          return okJson({ success: false, error: 'Simulation has no agents' })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()

      expect(wrapper.text()).toContain('Simulation has no agents')
    })

    it('shows error when check endpoint throws network error', async () => {
      const fetchFn = vi.fn(async () => {
        throw new Error('Network failure')
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()

      expect(wrapper.text()).toContain('Failed to check report status')
    })

    it('continues polling when progress fetch fails transiently', async () => {
      let progressFailCount = 0
      let sectionCallCount = 0
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return { ok: false, status: 404, json: async () => ({ success: false }) }
        }
        if (url.includes('/report/generate')) {
          return okJson({
            success: true,
            data: { report_id: 'rpt_retry', task_id: 'task_r', status: 'generating', already_generated: false },
          })
        }
        if (url.includes('/progress')) {
          progressFailCount++
          if (progressFailCount === 1) {
            throw new Error('Transient network error')
          }
          return okJson({ success: true, data: { progress: 100, message: 'Done' } })
        }
        if (url.includes('/sections')) {
          sectionCallCount++
          return okJson({
            success: true,
            data: {
              sections: [{ filename: 's1.md', section_index: 1, content: '## Recovered\n\nContent after retry.' }],
              total_sections: 1,
              is_complete: sectionCallCount >= 2,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()
      await flushPromises()

      expect(wrapper.text()).toContain('Recovered')
      expect(wrapper.text()).toContain('Generating next...')

      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      expect(wrapper.text()).not.toContain('Generating next...')
    })
  })

  describe('cleanup', () => {
    it('stops polling when component is unmounted', async () => {
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return { ok: false, status: 404, json: async () => ({ success: false }) }
        }
        if (url.includes('/report/generate')) {
          return okJson({
            success: true,
            data: { report_id: 'rpt_unmount', task_id: 'task_u', status: 'generating', already_generated: false },
          })
        }
        if (url.includes('/progress')) {
          return okJson({ success: true, data: { progress: 50, message: 'Still going...' } })
        }
        if (url.includes('/sections')) {
          return okJson({
            success: true,
            data: {
              sections: [{ filename: 's1.md', section_index: 1, content: '## Temp\n\nContent.' }],
              total_sections: 1,
              is_complete: false,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()
      await flushPromises()

      const callsBeforeUnmount = fetchFn.mock.calls.length
      wrapper.unmount()

      await vi.advanceTimersByTimeAsync(10000)

      expect(fetchFn.mock.calls.length).toBe(callsBeforeUnmount)
    })
  })

  describe('post-completion UI', () => {
    it('shows export button and chat link after generation completes', async () => {
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return okJson({
            success: true,
            data: { has_report: true, report_id: 'rpt_done', report_status: 'completed' },
          })
        }
        if (url.includes('/sections')) {
          return okJson({
            success: true,
            data: {
              sections: [{ filename: 's1.md', section_index: 1, content: '## Done\n\nFinal report.' }],
              total_sections: 1,
              is_complete: true,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()

      const exportBtn = wrapper.findAll('button').find((b) => b.text().includes('Export'))
      expect(exportBtn).toBeTruthy()

      const chatLink = wrapper.find('a[href="/chat/sim_e2e"]')
      expect(chatLink.exists()).toBe(true)
      expect(chatLink.text()).toContain('Ask Follow-Up')
    })

    it('extracts key findings from generated report', async () => {
      const fetchFn = vi.fn(async (url) => {
        if (url.includes('/report/check/')) {
          return okJson({
            success: true,
            data: { has_report: true, report_id: 'rpt_findings', report_status: 'completed' },
          })
        }
        if (url.includes('/sections')) {
          return okJson({
            success: true,
            data: {
              sections: [
                {
                  filename: 's1.md',
                  section_index: 1,
                  content: '## Analysis\n\n### Key Findings\n\n- Pipeline velocity increased 40%\n- Win rate improved from 22% to 31%\n- Average deal size grew by $15K\n\n### Next Steps\n\n- Scale outbound',
                },
              ],
              total_sections: 1,
              is_complete: true,
            },
          })
        }
        return { ok: false, json: async () => ({}) }
      })

      const wrapper = mountReportE2E(fetchFn)
      await flushPromises()

      expect(wrapper.text()).toContain('Pipeline velocity increased 40%')
      expect(wrapper.text()).toContain('Win rate improved from 22% to 31%')
      expect(wrapper.text()).toContain('Average deal size grew by $15K')
    })
  })
})

// === Component rendering tests ===

describe('ReportView', () => {
  let originalFetch

  beforeEach(() => {
    originalFetch = global.fetch
    vi.useFakeTimers()
  })

  afterEach(() => {
    global.fetch = originalFetch
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
