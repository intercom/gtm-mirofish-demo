import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ReportView from './ReportView.vue'

/**
 * E2E-style integration test for the report generation flow.
 * Exercises the full lifecycle: check → generate → poll → sections → complete.
 */

const mockRouterLink = {
  template: '<a :href="to"><slot /></a>',
  props: ['to'],
}

function okJson(data) {
  return { ok: true, json: async () => data }
}

function failJson(error, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => ({ success: false, error }) }
}

function mountReport(fetchFn) {
  global.fetch = fetchFn
  return mount(ReportView, {
    props: { taskId: 'sim_e2e' },
    global: {
      stubs: { 'router-link': mockRouterLink },
    },
  })
}

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
        // Step 1: check endpoint returns 404 (no existing report)
        if (url.includes('/report/check/')) {
          return { ok: false, status: 404, json: async () => ({ success: false }) }
        }

        // Step 2: generate endpoint starts generation
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

        // Step 3+: poll progress — simulate increasing progress
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

        // Step 3+: sections — simulate incremental delivery
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

      const wrapper = mountReport(fetchFn)

      // Initial mount triggers checkAndLoad → 404 → startGeneration
      await flushPromises()
      // startPolling fires pollProgress immediately
      await flushPromises()

      // After first poll: 1 section visible, still generating
      expect(wrapper.findAll('nav button').length).toBe(1)
      expect(wrapper.text()).toContain('Executive Summary')
      expect(wrapper.text()).toContain('Generating next...')

      // Advance timer for second poll (3s interval)
      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      // After second poll: 2 sections, still generating
      expect(wrapper.findAll('nav button').length).toBe(2)
      expect(wrapper.text()).toContain('Market Analysis')

      // Advance timer for third poll
      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      // After third poll: 3 sections, complete — polling should stop
      expect(wrapper.findAll('nav button').length).toBe(3)
      expect(wrapper.text()).toContain('Recommendations')
      expect(wrapper.text()).not.toContain('Generating next...')

      // Verify polling stopped: no more fetch calls after completion
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()
      await flushPromises()

      // Progress bar should show 45%
      expect(wrapper.text()).toContain('45%')
      const progressBar = wrapper.find('[style*="width"]')
      expect(progressBar.exists()).toBe(true)

      // Complete the generation
      pollDone = true
      await vi.advanceTimersByTimeAsync(3000)
      await flushPromises()

      // Progress bar should be gone (generating = false)
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()

      // Should render the cached report directly, no polling
      expect(wrapper.text()).toContain('Cached Report')
      expect(wrapper.text()).not.toContain('Generating next...')

      // No progress endpoint should have been called
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()

      // Report should render immediately
      expect(wrapper.findAll('nav button').length).toBe(2)
      expect(wrapper.text()).toContain('Existing Report')
      expect(wrapper.text()).not.toContain('Generating')

      // Never called generate or progress
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()
      await flushPromises()

      // Should be polling (generating indicator visible)
      expect(wrapper.text()).toContain('Generating next...')

      // Complete on next poll
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()

      expect(wrapper.text()).toContain('Simulation has no agents')
    })

    it('shows error when check endpoint throws network error', async () => {
      const fetchFn = vi.fn(async () => {
        throw new Error('Network failure')
      })

      const wrapper = mountReport(fetchFn)
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()
      await flushPromises()

      // First poll failed (progress threw), but sections still loaded
      expect(wrapper.text()).toContain('Recovered')
      expect(wrapper.text()).toContain('Generating next...')

      // Second poll succeeds and completes
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()
      await flushPromises()

      const callsBeforeUnmount = fetchFn.mock.calls.length
      wrapper.unmount()

      // Advance timers well beyond poll interval
      await vi.advanceTimersByTimeAsync(10000)

      // No additional fetch calls after unmount
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()

      // Export button visible
      const exportBtn = wrapper.findAll('button').find((b) => b.text().includes('Export'))
      expect(exportBtn).toBeTruthy()

      // Chat link points to correct path
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

      const wrapper = mountReport(fetchFn)
      await flushPromises()

      expect(wrapper.text()).toContain('Pipeline velocity increased 40%')
      expect(wrapper.text()).toContain('Win rate improved from 22% to 31%')
      expect(wrapper.text()).toContain('Average deal size grew by $15K')
    })
  })
})
