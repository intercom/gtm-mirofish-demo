import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import GraphView from '../GraphView.vue'

// Mock graphApi module
vi.mock('../../api/graph', () => ({
  graphApi: {
    getTask: vi.fn(),
    getData: vi.fn(),
  },
}))

import { graphApi } from '../../api/graph'

// Mock ResizeObserver (not available in happy-dom)
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = MockResizeObserver

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/graph/:taskId', name: 'graph', component: GraphView, props: true },
      { path: '/simulation/:taskId', name: 'simulation', component: { template: '<div />' } },
    ],
  })
}

function mountGraph(taskId = 'test-task-123') {
  const router = createTestRouter()
  return mount(GraphView, {
    props: { taskId },
    global: { plugins: [router] },
    attachTo: document.body,
  })
}

describe('GraphView', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Default: API rejects → triggers sample data fallback
    graphApi.getTask.mockRejectedValue(new Error('Not found'))
    graphApi.getData.mockRejectedValue(new Error('Not found'))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
    document.body.innerHTML = ''
  })

  it('mounts with building status initially', () => {
    const wrapper = mountGraph()
    expect(wrapper.text()).toContain('Building')
    expect(wrapper.text()).toContain('0%')
  })

  it('shows stats panel with zero counts initially', () => {
    const wrapper = mountGraph()
    expect(wrapper.find('[data-testid="node-count"]').text()).toBe('0')
    expect(wrapper.find('[data-testid="edge-count"]').text()).toBe('0')
  })

  it('loads sample data when API is unavailable', async () => {
    const wrapper = mountGraph()

    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    expect(wrapper.find('[data-testid="node-count"]').text()).not.toBe('0')
    expect(wrapper.find('[data-testid="edge-count"]').text()).not.toBe('0')
    expect(wrapper.text()).toContain('Complete')
  })

  it('shows correct type breakdown in stats', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    // Sample data: 12 personas, 12 topics, 8 relationships
    expect(wrapper.find('[data-testid="persona-count"]').text()).toBe('12')
    expect(wrapper.find('[data-testid="topic-count"]').text()).toBe('12')
    expect(wrapper.find('[data-testid="relationship-count"]').text()).toBe('8')
  })

  it('renders SVG canvas when graph data loads', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
  })

  it('creates node circles in SVG', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const circles = wrapper.findAll('circle')
    expect(circles.length).toBe(32) // 12 + 12 + 8
  })

  it('creates edge lines in SVG', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const lines = wrapper.findAll('line')
    expect(lines.length).toBeGreaterThan(0)
  })

  it('does not show detail panel initially', () => {
    const wrapper = mountGraph()
    expect(wrapper.find('[data-testid="detail-panel"]').exists()).toBe(false)
  })

  it('does not show continue button while building', () => {
    graphApi.getTask.mockResolvedValue({
      data: { data: { status: 'processing', progress: 50 } },
    })

    const wrapper = mountGraph()
    expect(wrapper.find('a[href*="simulation"]').exists()).toBe(false)
  })

  it('shows continue button when status is complete', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const link = wrapper.find('a')
    expect(link.exists()).toBe(true)
    expect(link.text()).toContain('Continue to Simulation')
    expect(link.attributes('href')).toContain('/simulation/test-task-123')
  })

  it('calls graphApi.getTask with the taskId', async () => {
    graphApi.getTask.mockResolvedValue({
      data: { data: { status: 'processing', progress: 45 } },
    })

    mountGraph('my-task')
    await flushPromises()

    expect(graphApi.getTask).toHaveBeenCalledWith('my-task')
  })

  it('updates progress from polling response', async () => {
    graphApi.getTask.mockResolvedValue({
      data: { data: { status: 'processing', progress: 65 } },
    })

    const wrapper = mountGraph()
    await flushPromises()

    expect(wrapper.text()).toContain('65%')
  })

  it('fetches graph data when task completes', async () => {
    graphApi.getTask.mockResolvedValue({
      data: {
        data: {
          status: 'completed',
          progress: 100,
          result: { graph_id: 'graph-abc' },
        },
      },
    })
    graphApi.getData.mockResolvedValue({
      data: {
        data: {
          nodes: [
            { uuid: 'n1', name: 'Test Person', labels: ['Person'], summary: 'A person', attributes: {} },
            { uuid: 'n2', name: 'Test Topic', labels: ['Topic'], summary: 'A topic', attributes: {} },
          ],
          edges: [
            { uuid: 'e1', source_node_uuid: 'n1', target_node_uuid: 'n2', name: 'discusses', fact: 'Test', fact_type: 'engagement' },
          ],
        },
      },
    })

    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    expect(graphApi.getData).toHaveBeenCalledWith('graph-abc')
    expect(wrapper.find('[data-testid="node-count"]').text()).toBe('2')
    expect(wrapper.find('[data-testid="edge-count"]').text()).toBe('1')
  })

  it('colors persona nodes with fin orange', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const circles = wrapper.findAll('circle')
    const personaCircle = circles.find((c) => c.attributes('fill') === '#ff5600')
    expect(personaCircle).toBeTruthy()
  })

  it('colors topic nodes with intercom blue', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const circles = wrapper.findAll('circle')
    const topicCircle = circles.find((c) => c.attributes('fill') === '#2068FF')
    expect(topicCircle).toBeTruthy()
  })

  it('colors relationship nodes with accent purple', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const circles = wrapper.findAll('circle')
    const relCircle = circles.find((c) => c.attributes('fill') === '#AA00FF')
    expect(relCircle).toBeTruthy()
  })

  it('scales node radius by degree (higher degree = larger)', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const circles = wrapper.findAll('circle')
    const radii = circles.map((c) => parseFloat(c.attributes('r')))
    const uniqueRadii = [...new Set(radii)]
    expect(uniqueRadii.length).toBeGreaterThan(1)
  })

  it('shows error state when task fails', async () => {
    graphApi.getTask.mockResolvedValue({
      data: { data: { status: 'failed', progress: 0 } },
    })

    const wrapper = mountGraph()
    await flushPromises()

    expect(wrapper.text()).toContain('Build Failed')
  })

  it('applies dark canvas background', () => {
    const wrapper = mountGraph()
    const root = wrapper.find('.bg-\\[\\#0a0a1a\\]')
    expect(root.exists()).toBe(true)
  })

  it('creates SVG with glow filter for nodes', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const filter = wrapper.find('filter#node-glow')
    expect(filter.exists()).toBe(true)
  })

  it('shows labels for high-degree nodes', async () => {
    const wrapper = mountGraph()
    await flushPromises()
    vi.advanceTimersByTime(100)
    await flushPromises()

    const texts = wrapper.findAll('text')
    expect(texts.length).toBeGreaterThan(0)
  })
})
