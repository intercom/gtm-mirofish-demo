import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import GraphView from '../GraphView.vue'

// Stub SVG methods that jsdom doesn't implement
beforeEach(() => {
  // SVGElement.prototype.getBBox is not in jsdom
  if (!SVGElement.prototype.getBBox) {
    SVGElement.prototype.getBBox = () => ({ x: 0, y: 0, width: 100, height: 100 })
  }
})

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/graph/:taskId', name: 'graph', component: GraphView, props: true },
      { path: '/simulation/:taskId', name: 'simulation', component: { template: '<div />' } },
    ],
  })
}

function mountGraphView(taskId = 'test-task-1') {
  const router = createTestRouter()
  return mount(GraphView, {
    props: { taskId },
    global: {
      plugins: [router],
    },
    attachTo: document.body,
  })
}

// --- Helper: build a mock task response at various stages ---
function mockTaskResponse(status, progress = 0, result = null) {
  return {
    success: true,
    data: {
      task_id: 'test-task-1',
      status,
      progress,
      message: `Status: ${status}`,
      result,
    },
  }
}

function mockGraphData() {
  return {
    success: true,
    data: {
      graph_id: 'graph-1',
      nodes: [
        { uuid: 'n1', name: 'Alice', labels: ['Entity', 'Person'], summary: 'A buyer persona' },
        { uuid: 'n2', name: 'AI Chat', labels: ['Entity', 'Topic'], summary: 'Product feature' },
        { uuid: 'n3', name: 'Onboarding', labels: ['Entity', 'Process'], summary: 'User flow' },
      ],
      edges: [
        { uuid: 'e1', source_node_uuid: 'n1', target_node_uuid: 'n2', name: 'evaluates', fact: 'Alice evaluates AI Chat' },
        { uuid: 'e2', source_node_uuid: 'n2', target_node_uuid: 'n3', name: 'part_of', fact: 'AI Chat is part of Onboarding' },
        { uuid: 'e3', source_node_uuid: 'n1', target_node_uuid: 'n3', name: 'uses', fact: 'Alice uses Onboarding' },
      ],
      node_count: 3,
      edge_count: 3,
    },
  }
}

describe('GraphView', () => {
  let fetchSpy

  beforeEach(() => {
    vi.useFakeTimers()
    fetchSpy = vi.spyOn(globalThis, 'fetch')
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('initial state', () => {
    it('renders with building status initially', () => {
      fetchSpy.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockTaskResponse('processing', 25)) })
      const wrapper = mountGraphView()
      expect(wrapper.text()).toContain('Building Graph...')
      wrapper.unmount()
    })

    it('displays the task ID', () => {
      fetchSpy.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockTaskResponse('processing')) })
      const wrapper = mountGraphView('my-task-42')
      expect(wrapper.text()).toContain('my-task-42')
      wrapper.unmount()
    })
  })

  describe('task polling', () => {
    it('polls the task API on mount', async () => {
      fetchSpy.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockTaskResponse('processing', 50)) })

      const wrapper = mountGraphView()
      await flushPromises()

      expect(fetchSpy).toHaveBeenCalledWith('/api/graph/task/test-task-1')
      wrapper.unmount()
    })

    it('shows progress percentage during build', async () => {
      fetchSpy.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockTaskResponse('processing', 75)) })

      const wrapper = mountGraphView()
      await flushPromises()

      expect(wrapper.text()).toContain('75%')
      wrapper.unmount()
    })

    it('transitions to complete when task finishes', async () => {
      const taskResult = { graph_id: 'graph-1', node_count: 3, edge_count: 3 }
      fetchSpy
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockTaskResponse('completed', 100, taskResult)) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockGraphData()) })

      const wrapper = mountGraphView()
      await flushPromises()

      expect(wrapper.text()).toContain('Complete')
      wrapper.unmount()
    })

    it('shows failed state on build failure', async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { task_id: 'test-task-1', status: 'failed', message: 'Zep API error', progress: 0 },
        }),
      })

      const wrapper = mountGraphView()
      await flushPromises()

      expect(wrapper.text()).toContain('Failed')
      expect(wrapper.text()).toContain('Graph build failed')
      wrapper.unmount()
    })
  })

  describe('demo fallback', () => {
    it('loads demo data when backend is unreachable', async () => {
      fetchSpy.mockRejectedValue(new Error('Network error'))

      const wrapper = mountGraphView()
      await flushPromises()

      expect(wrapper.text()).toContain('Complete')
      expect(wrapper.text()).toContain('12 nodes')
      expect(wrapper.text()).toContain('15 edges')
      wrapper.unmount()
    })

    it('loads demo data when task is not found', async () => {
      // First call: task not found (404)
      // Second call: graph data not found (also 404)
      fetchSpy
        .mockResolvedValueOnce({ ok: false, status: 404 })
        .mockResolvedValueOnce({ ok: false, status: 404 })

      const wrapper = mountGraphView()
      await flushPromises()

      expect(wrapper.text()).toContain('Complete')
      expect(wrapper.text()).toContain('12 nodes')
      wrapper.unmount()
    })
  })

  describe('graph data loading', () => {
    it('fetches graph data after task completion', async () => {
      const taskResult = { graph_id: 'graph-1' }
      fetchSpy
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockTaskResponse('completed', 100, taskResult)) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockGraphData()) })

      const wrapper = mountGraphView()
      await flushPromises()

      // First call: task poll, second call: graph data
      expect(fetchSpy).toHaveBeenCalledTimes(2)
      expect(fetchSpy).toHaveBeenLastCalledWith('/api/graph/data/graph-1')

      expect(wrapper.text()).toContain('3 nodes')
      expect(wrapper.text()).toContain('3 edges')
      wrapper.unmount()
    })
  })

  describe('stats panel', () => {
    it('shows entity type breakdown', async () => {
      fetchSpy.mockRejectedValue(new Error('offline'))

      const wrapper = mountGraphView()
      await flushPromises()

      // Demo data has Persona, Topic, Process, Feature, Event types
      expect(wrapper.text()).toContain('Entity Types')
      expect(wrapper.text()).toContain('Persona')
      expect(wrapper.text()).toContain('Topic')
      wrapper.unmount()
    })
  })

  describe('node detail panel', () => {
    it('is hidden by default', async () => {
      fetchSpy.mockRejectedValue(new Error('offline'))
      const wrapper = mountGraphView()
      await flushPromises()

      // No detail panel visible
      expect(wrapper.text()).not.toContain('Summary')
      expect(wrapper.text()).not.toContain('Centrality')
      wrapper.unmount()
    })
  })

  describe('continue button', () => {
    it('shows continue button when complete', async () => {
      fetchSpy.mockRejectedValue(new Error('offline'))
      const wrapper = mountGraphView()
      await flushPromises()

      const link = wrapper.find('a[href*="simulation"]')
      expect(link.exists()).toBe(true)
      expect(link.text()).toContain('Continue to Simulation')
      wrapper.unmount()
    })

    it('hides continue button during build', async () => {
      fetchSpy.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockTaskResponse('processing', 30)) })
      const wrapper = mountGraphView()
      await flushPromises()

      const link = wrapper.find('a[href*="simulation"]')
      expect(link.exists()).toBe(false)
      wrapper.unmount()
    })
  })

  describe('cleanup', () => {
    it('clears polling timer on unmount', async () => {
      fetchSpy.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockTaskResponse('processing', 10)) })
      const clearSpy = vi.spyOn(globalThis, 'clearInterval')

      const wrapper = mountGraphView()
      await flushPromises()
      wrapper.unmount()

      expect(clearSpy).toHaveBeenCalled()
    })
  })
})

describe('GraphView color mapping', () => {
  // Test the color logic by mounting and checking demo data rendering
  let fetchSpy

  beforeEach(() => {
    vi.useFakeTimers()
    fetchSpy = vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'))
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('renders color dots in stats panel for each entity type', async () => {
    const wrapper = mountGraphView()
    await flushPromises()

    // Stats panel has colored dots (spans with inline background color)
    const colorDots = wrapper.findAll('.rounded-full.flex-shrink-0')
    expect(colorDots.length).toBeGreaterThan(0)
    wrapper.unmount()
  })
})
