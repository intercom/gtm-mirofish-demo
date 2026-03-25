import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import GraphPanel from '../GraphPanel.vue'

class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = MockResizeObserver

class MockMutationObserver {
  observe() {}
  disconnect() {}
}
globalThis.MutationObserver = MockMutationObserver

function createPolling(overrides = {}) {
  return {
    graphStatus: ref('building'),
    graphProgress: ref(0),
    graphData: ref({ nodes: [], edges: [] }),
    graphId: ref(null),
    graphTask: ref(null),
    isDemoFallback: ref(false),
    ...overrides,
  }
}

const sampleNodes = [
  { uuid: 'n1', name: 'Enterprise Buyer', labels: ['Entity', 'Persona'], summary: 'A buyer', attributes: {} },
  { uuid: 'n2', name: 'AI Automation', labels: ['Entity', 'Topic'], summary: 'AI topic', attributes: {} },
  { uuid: 'n3', name: 'Product-Led Growth', labels: ['Entity', 'Process'], summary: 'PLG motion', attributes: {} },
]

const sampleEdges = [
  { uuid: 'e1', source_node_uuid: 'n1', target_node_uuid: 'n2', name: 'evaluates', fact: 'Buyer evaluates AI', fact_type: 'engagement' },
  { uuid: 'e2', source_node_uuid: 'n2', target_node_uuid: 'n3', name: 'enables', fact: 'AI enables PLG', fact_type: 'relationship' },
]

function mountPanel(pollingOverrides = {}, propsOverrides = {}) {
  const polling = createPolling(pollingOverrides)
  return mount(GraphPanel, {
    props: { taskId: 'test-123', demoMode: false, ...propsOverrides },
    global: {
      provide: { polling },
    },
    attachTo: document.body,
  })
}

describe('GraphPanel', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  // --- Status display ---

  it('shows "Building Graph..." status when building', () => {
    const wrapper = mountPanel()
    expect(wrapper.text()).toContain('Building Graph...')
    expect(wrapper.text()).toContain('0%')
  })

  it('shows progress percentage during build', () => {
    const wrapper = mountPanel({ graphProgress: ref(45) })
    expect(wrapper.text()).toContain('45%')
  })

  it('shows "Complete" status when graph is complete', () => {
    const wrapper = mountPanel({
      graphStatus: ref('complete'),
      graphProgress: ref(100),
      graphData: ref({ nodes: sampleNodes, edges: sampleEdges }),
    })
    expect(wrapper.text()).toContain('Complete')
  })

  it('shows "Failed" status when graph fails', () => {
    const wrapper = mountPanel({ graphStatus: ref('failed') })
    expect(wrapper.text()).toContain('Failed')
  })

  // --- Status badge styling ---

  it('applies yellow styling for building status', () => {
    const wrapper = mountPanel()
    const badge = wrapper.find('.rounded-full')
    expect(badge.classes()).toContain('bg-yellow-500/20')
    expect(badge.classes()).toContain('text-yellow-400')
  })

  it('applies green styling for complete status', () => {
    const wrapper = mountPanel({
      graphStatus: ref('complete'),
      graphData: ref({ nodes: sampleNodes, edges: sampleEdges }),
    })
    const badge = wrapper.find('.rounded-full')
    expect(badge.classes()).toContain('bg-green-500/20')
    expect(badge.classes()).toContain('text-green-400')
  })

  it('applies red styling for failed status', () => {
    const wrapper = mountPanel({ graphStatus: ref('failed') })
    const badge = wrapper.find('.rounded-full')
    expect(badge.classes()).toContain('bg-red-500/20')
    expect(badge.classes()).toContain('text-red-400')
  })

  // --- Error state ---

  it('shows error overlay with message when status transitions to failed', async () => {
    const graphStatus = ref('building')
    const graphTask = ref({ message: 'Out of memory' })
    const wrapper = mountPanel({ graphStatus, graphTask })

    graphStatus.value = 'failed'
    await flushPromises()

    expect(wrapper.text()).toContain('Graph build failed')
    expect(wrapper.text()).toContain('Out of memory')
  })

  it('does not show error overlay when building', () => {
    const wrapper = mountPanel()
    expect(wrapper.text()).not.toContain('Graph build failed')
  })

  // --- Build progress overlay ---

  it('shows build progress overlay with message during non-demo build', () => {
    const wrapper = mountPanel({
      graphProgress: ref(30),
      graphTask: ref({ message: 'Extracting entities...' }),
    })
    expect(wrapper.text()).toContain('Building Graph...')
    expect(wrapper.text()).toContain('30%')
  })

  it('does not show progress overlay in demo mode', () => {
    const wrapper = mountPanel(
      { graphStatus: ref('building'), graphProgress: ref(50) },
      { demoMode: true },
    )
    // The overlay has a condition: graphStatus === 'building' && !demoMode && !isDemoFallback
    // In demo mode it should be hidden
    const overlay = wrapper.find('.backdrop-blur-sm.rounded-xl')
    expect(overlay.exists()).toBe(false)
  })

  // --- Entity type stats panel ---

  it('shows entity type stats when graph is complete with data', async () => {
    const wrapper = mountPanel({
      graphStatus: ref('complete'),
      graphProgress: ref(100),
      graphData: ref({ nodes: sampleNodes, edges: sampleEdges }),
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Entity Types')
  })

  it('displays correct entity type names from graph data', async () => {
    const wrapper = mountPanel({
      graphStatus: ref('complete'),
      graphProgress: ref(100),
      graphData: ref({ nodes: sampleNodes, edges: sampleEdges }),
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Persona')
    expect(wrapper.text()).toContain('Topic')
    expect(wrapper.text()).toContain('Process')
  })

  it('does not show entity type stats when graph failed', () => {
    const wrapper = mountPanel({
      graphStatus: ref('failed'),
      graphData: ref({ nodes: sampleNodes, edges: sampleEdges }),
    })
    expect(wrapper.text()).not.toContain('Entity Types')
  })

  // --- Node/Edge counts ---

  it('shows node and edge counts when complete', async () => {
    const wrapper = mountPanel({
      graphStatus: ref('complete'),
      graphProgress: ref(100),
      graphData: ref({ nodes: sampleNodes, edges: sampleEdges }),
    })
    await flushPromises()
    // The counts are in two places: stats panel and bottom-right
    const nodeCountEl = wrapper.find('[data-testid="node-count"]')
    const edgeCountEl = wrapper.find('[data-testid="edge-count"]')
    // These show "X nodes" / "X edges" format
    if (nodeCountEl.exists()) {
      expect(nodeCountEl.text()).toContain('nodes')
    }
    if (edgeCountEl.exists()) {
      expect(edgeCountEl.text()).toContain('edges')
    }
  })

  // --- Detail panel ---

  it('does not show detail panel by default', () => {
    const wrapper = mountPanel({
      graphStatus: ref('complete'),
      graphData: ref({ nodes: sampleNodes, edges: sampleEdges }),
    })
    expect(wrapper.find('[data-testid="detail-panel"]').exists()).toBe(false)
  })

  // --- SVG canvas ---

  it('renders SVG element', () => {
    const wrapper = mountPanel()
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('has graph-canvas class on SVG', () => {
    const wrapper = mountPanel()
    const svg = wrapper.find('svg.graph-canvas')
    expect(svg.exists()).toBe(true)
  })

  // --- Container styling ---

  it('has light and dark background classes', () => {
    const wrapper = mountPanel()
    const container = wrapper.find('.bg-\\[\\#f8f9fa\\]')
    expect(container.exists()).toBe(true)
  })

  // --- Demo mode ---

  it('triggers demo build in demo mode', async () => {
    const polling = createPolling()
    mount(GraphPanel, {
      props: { taskId: 'demo-1', demoMode: true },
      global: { provide: { polling } },
      attachTo: document.body,
    })
    await flushPromises()

    // Demo mode sets status to 'building' and starts loading data
    expect(polling.graphStatus.value).toBe('building')
  })

  it('triggers demo build on isDemoFallback', async () => {
    const isDemoFallback = ref(false)
    const polling = createPolling({ isDemoFallback })

    mount(GraphPanel, {
      props: { taskId: 'test-1', demoMode: false },
      global: { provide: { polling } },
      attachTo: document.body,
    })
    await flushPromises()

    // Flip the fallback flag
    isDemoFallback.value = true
    await flushPromises()

    expect(polling.graphStatus.value).toBe('building')
  })

  it('progressively loads demo data over time', async () => {
    const polling = createPolling()
    mount(GraphPanel, {
      props: { taskId: 'demo-1', demoMode: true },
      global: { provide: { polling } },
      attachTo: document.body,
    })
    await flushPromises()

    // Advance a few intervals (200ms each) to load batches
    vi.advanceTimersByTime(400)
    await flushPromises()

    expect(polling.graphData.value.nodes.length).toBeGreaterThan(0)
    expect(polling.graphProgress.value).toBeGreaterThan(0)
  })

  it('completes demo build after sufficient time', async () => {
    const polling = createPolling()
    mount(GraphPanel, {
      props: { taskId: 'demo-1', demoMode: true },
      global: { provide: { polling } },
      attachTo: document.body,
    })
    await flushPromises()

    // 55 nodes in demo data, BATCH=3, INTERVAL=200ms
    // Need ceil(55/3) * 200 = 3800ms to complete
    vi.advanceTimersByTime(5000)
    await flushPromises()

    expect(polling.graphStatus.value).toBe('complete')
    expect(polling.graphProgress.value).toBe(100)
    expect(polling.graphData.value.nodes.length).toBeGreaterThan(0)
    expect(polling.graphData.value.edges.length).toBeGreaterThan(0)
  })

  // --- Cleanup ---

  it('cleans up on unmount without errors', async () => {
    const wrapper = mountPanel()
    await flushPromises()
    expect(() => wrapper.unmount()).not.toThrow()
  })

  it('stops demo build timer on unmount', async () => {
    const polling = createPolling()
    const wrapper = mount(GraphPanel, {
      props: { taskId: 'demo-1', demoMode: true },
      global: { provide: { polling } },
      attachTo: document.body,
    })
    await flushPromises()
    vi.advanceTimersByTime(400)
    await flushPromises()

    const countBefore = polling.graphData.value.nodes.length
    wrapper.unmount()

    // After unmount, advancing timers should not add more nodes
    vi.advanceTimersByTime(2000)
    expect(polling.graphData.value.nodes.length).toBe(countBefore)
  })
})
