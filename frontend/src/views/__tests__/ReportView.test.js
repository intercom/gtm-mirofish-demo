import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import ReportView from '../ReportView.vue'

vi.mock('../../services/api.js', () => ({
  generateReport: vi.fn(),
  getReportGenerateStatus: vi.fn(),
  getReportSections: vi.fn(),
  pollTask: vi.fn(),
}))

import {
  generateReport,
  getReportSections,
  pollTask,
} from '../../services/api.js'

function createTestRouter(simulationId = 'sim-123') {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/report/:taskId',
        name: 'report',
        component: ReportView,
        props: true,
      },
      {
        path: '/chat/:taskId',
        name: 'chat',
        component: { template: '<div />' },
      },
      {
        path: '/simulation/:taskId',
        name: 'simulation',
        component: { template: '<div />' },
      },
    ],
  })
}

function mountReport(taskId = 'task-abc') {
  const router = createTestRouter()
  router.push({ path: `/report/${taskId}`, query: { simulationId: 'sim-123' } })
  return mount(ReportView, {
    props: { taskId },
    global: { plugins: [router] },
  })
}

describe('ReportView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows loading spinner while generating', async () => {
    generateReport.mockReturnValue(new Promise(() => {})) // never resolves
    const wrapper = mountReport()
    await flushPromises()

    expect(wrapper.text()).toContain('Generating predictive report')
  })

  it('shows progress bar during generation', async () => {
    generateReport.mockReturnValue(new Promise(() => {}))
    const wrapper = mountReport()
    await flushPromises()

    expect(wrapper.text()).toContain('Starting report generation')
  })

  it('renders report chapters after successful generation', async () => {
    generateReport.mockResolvedValue({
      data: { report_id: 'rpt-1', task_id: 't-1', already_generated: true },
    })
    getReportSections.mockResolvedValue({
      data: {
        sections: [
          { content: '# Executive Summary\nThis is the summary.' },
          { content: '# Key Findings\nThese are the findings.' },
        ],
      },
    })

    const wrapper = mountReport()
    await flushPromises()

    expect(wrapper.text()).toContain('Executive Summary')
    expect(wrapper.text()).toContain('Key Findings')
    expect(wrapper.text()).toContain('This is the summary.')
  })

  it('shows ErrorState with retry on failure', async () => {
    generateReport.mockRejectedValue(new Error('API timeout'))
    const wrapper = mountReport()
    await flushPromises()

    expect(wrapper.text()).toContain('Report generation failed')
    expect(wrapper.text()).toContain('API timeout')
    expect(wrapper.find('button').text()).toContain('Try Again')
  })

  it('retries generation when retry button is clicked', async () => {
    generateReport.mockRejectedValueOnce(new Error('Server error'))
    const wrapper = mountReport()
    await flushPromises()

    expect(wrapper.text()).toContain('Report generation failed')

    // Now make it succeed on retry
    generateReport.mockResolvedValueOnce({
      data: { report_id: 'rpt-2', task_id: 't-2', already_generated: true },
    })
    getReportSections.mockResolvedValue({
      data: { sections: [{ content: '# Results\nGood results.' }] },
    })

    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(generateReport).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Results')
  })

  it('shows EmptyState when report has no sections', async () => {
    generateReport.mockResolvedValue({
      data: { report_id: 'rpt-3', task_id: 't-3', already_generated: true },
    })
    getReportSections.mockResolvedValue({
      data: { sections: [] },
    })

    const wrapper = mountReport()
    await flushPromises()

    expect(wrapper.text()).toContain('No report sections')
    expect(wrapper.text()).toContain('Back to Simulation')
  })

  it('shows Ask Follow-Up link after successful generation', async () => {
    generateReport.mockResolvedValue({
      data: { report_id: 'rpt-4', task_id: 't-4', already_generated: true },
    })
    getReportSections.mockResolvedValue({
      data: { sections: [{ content: '# Summary\nDone.' }] },
    })

    const wrapper = mountReport()
    await flushPromises()

    const link = wrapper.find('a[href*="chat"]')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('Ask Follow-Up')
  })

  it('hides Ask Follow-Up link when in error state', async () => {
    generateReport.mockRejectedValue(new Error('Failed'))
    const wrapper = mountReport()
    await flushPromises()

    const link = wrapper.find('a[href*="chat"]')
    expect(link.exists()).toBe(false)
  })

  it('allows switching between chapters', async () => {
    generateReport.mockResolvedValue({
      data: { report_id: 'rpt-5', task_id: 't-5', already_generated: true },
    })
    getReportSections.mockResolvedValue({
      data: {
        sections: [
          { content: '# Chapter One\nFirst chapter content.' },
          { content: '# Chapter Two\nSecond chapter content.' },
        ],
      },
    })

    const wrapper = mountReport()
    await flushPromises()

    expect(wrapper.text()).toContain('First chapter content')

    // Click second chapter
    const buttons = wrapper.findAll('button')
    const chapterTwoBtn = buttons.find((b) => b.text().includes('Chapter Two'))
    await chapterTwoBtn.trigger('click')

    expect(wrapper.text()).toContain('Second chapter content')
  })
})
