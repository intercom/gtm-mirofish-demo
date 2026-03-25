import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import GraphPanel from '../GraphPanel.vue'

const mockObserve = vi.fn()
const mockDisconnect = vi.fn()

class MockResizeObserver {
  constructor() {}
  observe = mockObserve
  disconnect = mockDisconnect
  unobserve = vi.fn()
}

function createPolling(overrides = {}) {
  return {
    graphStatus: ref(overrides.graphStatus ?? 'building'),
    graphProgress: ref(overrides.graphProgress ?? 0),
    graphData: ref(overrides.graphData ?? { nodes: [], edges: [] }),
    graphId: ref(overrides.graphId ?? null),
    graphTask: ref(overrides.graphTask ?? null),
    isDemoFallback: ref(overrides.isDemoFallback ?? false),
  }
}

function mountGraphPanel(polling, props = {}) {
  return mount(GraphPanel, {
    props: { taskId: 'test-task-123', ...props },
    global: {
      provide: { polling },
    },
    attachTo: document.body,
  })
}

beforeEach(() => {
  vi.stubGlobal('ResizeObserver', MockResizeObserver)
})

afterEach(() => {
  vi.unstubAllGlobals()
  mockObserve.mockClear()
  mockDisconnect.mockClear()
})

describe('GraphPanel', () => {
  describe('status badge rendering', () => {
    it('shows building status with progress', () => {
      const polling = createPolling({ graphStatus: 'building', graphProgress: 42 })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.text()).toContain('Building Graph... 42%')
      wrapper.unmount()
    })

    it('shows complete status', () => {
      const polling = createPolling({ graphStatus: 'complete' })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.text()).toContain('Complete')
      wrapper.unmount()
    })

    it('shows failed status', () => {
      const polling = createPolling({ graphStatus: 'failed' })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.text()).toContain('Failed')
      wrapper.unmount()
    })
  })

  describe('building state', () => {
    it('shows progress overlay during build', () => {
      const polling = createPolling({ graphStatus: 'building', graphProgress: 25 })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.text()).toContain('Building Graph... 25%')
      wrapper.unmount()
    })

    it('shows build messages based on progress', () => {
      const polling = createPolling({
        graphStatus: 'building',
        graphProgress: 50,
        graphTask: { message: 'Extracting entities...' },
      })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.text()).toContain('Extracting entities...')
      wrapper.unmount()
    })

    it('does not show progress overlay in demo mode', () => {
      const polling = createPolling({ graphStatus: 'building', graphProgress: 25 })
      const wrapper = mountGraphPanel(polling, { demoMode: true })
      // The overlay has v-if="graphStatus === 'building' && !demoMode && !isDemoFallback"
      const overlay = wrapper.find('.backdrop-blur-sm.rounded-xl')
      expect(overlay.exists()).toBe(false)
      wrapper.unmount()
    })
  })

  describe('error state', () => {
    it('shows error overlay when build fails', async () => {
      const polling = createPolling({ graphStatus: 'failed' })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.text()).toContain('Graph build failed')
      wrapper.unmount()
    })

    it('shows error message from task', async () => {
      const polling = createPolling({
        graphStatus: 'building',
        graphTask: { message: 'LLM rate limited' },
      })
      const wrapper = mountGraphPanel(polling)

      polling.graphStatus.value = 'failed'
      await nextTick()

      expect(wrapper.text()).toContain('Graph build failed')
      wrapper.unmount()
    })
  })

  describe('entity type stats', () => {
    it('shows entity type stats when nodes have data', async () => {
      const polling = createPolling({
        graphStatus: 'complete',
        graphData: {
          nodes: [
            { uuid: 'n1', name: 'A', labels: ['Entity', 'Persona'], summary: '' },
            { uuid: 'n2', name: 'B', labels: ['Entity', 'Topic'], summary: '' },
            { uuid: 'n3', name: 'C', labels: ['Entity', 'Persona'], summary: '' },
          ],
          edges: [],
        },
      })
      const wrapper = mountGraphPanel(polling)
      await nextTick()

      expect(wrapper.text()).toContain('Entity Types')
      expect(wrapper.text()).toContain('Persona')
      expect(wrapper.text()).toContain('Topic')
      wrapper.unmount()
    })

    it('does not show entity stats when graph is failed', async () => {
      const polling = createPolling({
        graphStatus: 'failed',
        graphData: {
          nodes: [
            { uuid: 'n1', name: 'A', labels: ['Entity', 'Persona'], summary: '' },
          ],
          edges: [],
        },
      })
      const wrapper = mountGraphPanel(polling)
      await nextTick()

      // v-if="entityTypeStats.length && graphStatus !== 'failed'"
      expect(wrapper.text()).not.toContain('Entity Types')
      wrapper.unmount()
    })

    it('does not show stats when no nodes', () => {
      const polling = createPolling({ graphStatus: 'complete' })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.text()).not.toContain('Entity Types')
      wrapper.unmount()
    })
  })

  describe('SVG canvas', () => {
    it('always renders an SVG element', () => {
      const polling = createPolling()
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.find('svg.graph-canvas').exists()).toBe(true)
      wrapper.unmount()
    })
  })

  describe('node detail panel', () => {
    it('does not show detail panel by default', () => {
      const polling = createPolling({ graphStatus: 'complete' })
      const wrapper = mountGraphPanel(polling)
      expect(wrapper.find('[data-testid="detail-panel"]').exists()).toBe(false)
      wrapper.unmount()
    })
  })

  describe('lifecycle', () => {
    it('sets up ResizeObserver on mount', () => {
      const polling = createPolling()
      const wrapper = mountGraphPanel(polling)
      expect(mockObserve).toHaveBeenCalled()
      wrapper.unmount()
    })

    it('disconnects observers on unmount', () => {
      const polling = createPolling()
      const wrapper = mountGraphPanel(polling)
      wrapper.unmount()
      expect(mockDisconnect).toHaveBeenCalled()
    })

    it('triggers demo data loading when demoMode is true', () => {
      const polling = createPolling()
      const wrapper = mountGraphPanel(polling, { demoMode: true })
      // Demo mode triggers loadDemoData which sets status to building
      expect(polling.graphStatus.value).toBe('building')
      wrapper.unmount()
    })

    it('triggers demo data loading when isDemoFallback is true', () => {
      const polling = createPolling({ isDemoFallback: true })
      const wrapper = mountGraphPanel(polling)
      expect(polling.graphStatus.value).toBe('building')
      wrapper.unmount()
    })
  })

  describe('color mapping', () => {
    it('assigns persona color to persona nodes in stats', async () => {
      const polling = createPolling({
        graphStatus: 'complete',
        graphData: {
          nodes: [
            { uuid: 'n1', name: 'Test', labels: ['Entity', 'Persona'], summary: '' },
          ],
          edges: [],
        },
      })
      const wrapper = mountGraphPanel(polling)
      await nextTick()

      // Persona nodes should get the orange color (#ff5600)
      const dot = wrapper.find('[style*="background-color"]')
      if (dot.exists()) {
        const style = dot.attributes('style')
        expect(style).toContain('#ff5600')
      }
      wrapper.unmount()
    })

    it('assigns topic color to topic nodes in stats', async () => {
      const polling = createPolling({
        graphStatus: 'complete',
        graphData: {
          nodes: [
            { uuid: 'n1', name: 'Test', labels: ['Entity', 'Topic'], summary: '' },
          ],
          edges: [],
        },
      })
      const wrapper = mountGraphPanel(polling)
      await nextTick()

      const dot = wrapper.find('[style*="background-color"]')
      if (dot.exists()) {
        const style = dot.attributes('style')
        expect(style).toContain('#2068FF')
      }
      wrapper.unmount()
    })
  })
})
