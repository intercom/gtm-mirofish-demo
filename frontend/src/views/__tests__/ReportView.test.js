import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ReportView from '../ReportView.vue'

const mockRouterLink = {
  template: '<a :href="to"><slot /></a>',
  props: ['to'],
}

function mockFetch(responses) {
  const calls = []
  let callIndex = 0
  const fn = vi.fn(async (url, opts) => {
    calls.push({ url, opts })
    const handler = responses[callIndex++]
    if (!handler) return { ok: false, json: async () => ({}) }
    return handler(url, opts)
  })
  fn.calls = calls
  return fn
}

function okJson(data) {
  return () => ({ ok: true, json: async () => data })
}

function notFound() {
  return () => ({ ok: false, status: 404, json: async () => ({ success: false }) })
}

const completedCheckResponse = okJson({
  success: true,
  data: {
    simulation_id: 'sim_123',
    has_report: true,
    report_status: 'completed',
    report_id: 'report_abc',
    interview_unlocked: true,
  },
})

const sectionsResponse = okJson({
  success: true,
  data: {
    report_id: 'report_abc',
    sections: [
      {
        filename: 'section_01.md',
        section_index: 1,
        content: '## Executive Summary\n\nThis report analyzes the GTM simulation results.',
      },
      {
        filename: 'section_02.md',
        section_index: 2,
        content:
          '## Key Findings\n\n### Key Findings\n\n- Revenue grew 25% quarter-over-quarter\n- Enterprise segment outperformed SMB by 3x\n- Churn reduced to 4.2% from 6.1%',
      },
      {
        filename: 'section_03.md',
        section_index: 3,
        content: '## Recommendations\n\nFocus on enterprise expansion.',
      },
    ],
    total_sections: 3,
    is_complete: true,
  },
})

function mountReport(fetchImpl) {
  global.fetch = fetchImpl
  return mount(ReportView, {
    props: { taskId: 'sim_123' },
    global: {
      stubs: { 'router-link': mockRouterLink },
    },
  })
}

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

  it('renders loading state initially', () => {
    const fetchFn = mockFetch([
      // check endpoint hangs
      () => new Promise(() => {}),
    ])
    const wrapper = mountReport(fetchFn)
    expect(wrapper.text()).toContain('Generating')
  })

  it('loads completed report and renders chapters in sidebar', async () => {
    const fetchFn = mockFetch([completedCheckResponse, sectionsResponse])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    const buttons = wrapper.findAll('nav button')
    expect(buttons.length).toBe(3)
    expect(buttons[0].text()).toContain('Executive Summary')
    expect(buttons[1].text()).toContain('Key Findings')
    expect(buttons[2].text()).toContain('Recommendations')
  })

  it('renders markdown content for active chapter', async () => {
    const fetchFn = mockFetch([completedCheckResponse, sectionsResponse])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    const article = wrapper.find('article')
    expect(article.exists()).toBe(true)
    expect(article.html()).toContain('analyzes the GTM simulation')
  })

  it('switches chapters when sidebar button is clicked', async () => {
    const fetchFn = mockFetch([completedCheckResponse, sectionsResponse])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    const buttons = wrapper.findAll('nav button')
    await buttons[2].trigger('click')

    const article = wrapper.find('article')
    expect(article.html()).toContain('enterprise expansion')
  })

  it('extracts key findings into blue callout boxes', async () => {
    const fetchFn = mockFetch([completedCheckResponse, sectionsResponse])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    expect(wrapper.text()).toContain('Key Findings')
    expect(wrapper.text()).toContain('Revenue grew 25%')
    expect(wrapper.text()).toContain('Enterprise segment outperformed')
    expect(wrapper.text()).toContain('Churn reduced to 4.2%')

    // Verify callout containers exist (numbered badges with findings)
    const calloutHtml = wrapper.html()
    expect(calloutHtml).toContain('rgba(32,104,255')
    expect(calloutHtml).toContain('Revenue grew 25%')
  })

  it('shows export button when report is loaded', async () => {
    const fetchFn = mockFetch([completedCheckResponse, sectionsResponse])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    const exportBtn = wrapper.find('button')
    expect(exportBtn.text()).toContain('Export Markdown')
  })

  it('triggers report generation when no report exists', async () => {
    const generateResponse = okJson({
      success: true,
      data: {
        simulation_id: 'sim_123',
        report_id: 'report_new',
        task_id: 'task_1',
        status: 'generating',
        already_generated: false,
      },
    })

    const progressResponse = okJson({
      success: true,
      data: { progress: 30, message: 'Generating section 1...' },
    })

    const incompleteSections = okJson({
      success: true,
      data: {
        report_id: 'report_new',
        sections: [
          {
            filename: 'section_01.md',
            section_index: 1,
            content: '## Overview\n\nFirst section content.',
          },
        ],
        total_sections: 1,
        is_complete: false,
      },
    })

    const fetchFn = mockFetch([
      notFound(),
      generateResponse,
      progressResponse,
      incompleteSections,
    ])

    const wrapper = mountReport(fetchFn)
    await flushPromises()

    // Poll fires immediately after startPolling
    await flushPromises()

    // Should show the first section in sidebar
    const buttons = wrapper.findAll('nav button')
    expect(buttons.length).toBe(1)
    expect(buttons[0].text()).toContain('Overview')

    // Should still show generating indicator
    expect(wrapper.text()).toContain('Generating next...')
  })

  it('shows previous/next chapter navigation when report is complete', async () => {
    const fetchFn = mockFetch([completedCheckResponse, sectionsResponse])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    expect(wrapper.text()).toContain('Previous Chapter')
    expect(wrapper.text()).toContain('Next Chapter')
    expect(wrapper.text()).toContain('1 of 3')
  })

  it('calls download endpoint when export is clicked', async () => {
    const fetchFn = mockFetch([completedCheckResponse, sectionsResponse])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => {})
    const exportBtn = wrapper.findAll('button').find((b) => b.text().includes('Export'))
    await exportBtn.trigger('click')

    expect(openSpy).toHaveBeenCalledWith('/api/report/report_abc/download', '_blank')
    openSpy.mockRestore()
  })

  it('shows error state when check fails', async () => {
    const fetchFn = mockFetch([
      () => {
        throw new Error('Network error')
      },
    ])
    const wrapper = mountReport(fetchFn)
    await flushPromises()

    expect(wrapper.text()).toContain('Failed to check report status')
  })
})
