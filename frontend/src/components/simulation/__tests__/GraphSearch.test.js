import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import GraphSearch from '../GraphSearch.vue'

vi.mock('../../../api/graph', () => ({
  graphApi: {
    search: vi.fn().mockRejectedValue(new Error('no backend')),
  },
}))

const sampleGraphData = {
  nodes: [
    { uuid: 'n1', name: 'VP Sales', labels: ['Entity', 'Persona'], summary: 'Senior VP of Sales at TechCorp' },
    { uuid: 'n2', name: 'AI Platform', labels: ['Entity', 'Topic'], summary: 'ML platform product' },
    { uuid: 'n3', name: 'Migration', labels: ['Entity', 'Topic'], summary: 'Platform migration strategy' },
  ],
  edges: [
    { name: 'evaluates', fact: 'VP Sales evaluates AI Platform for team use', source: 'n1', target: 'n2' },
  ],
}

function mountSearch(props = {}) {
  return mount(GraphSearch, {
    props: {
      graphData: sampleGraphData,
      ...props,
    },
  })
}

async function typeAndSearch(wrapper, text) {
  const input = wrapper.find('input[type="text"]')
  await input.setValue(text)
  vi.advanceTimersByTime(300)
  await flushPromises()
  await nextTick()
}

describe('GraphSearch', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders search input with placeholder', () => {
    const wrapper = mountSearch()
    const input = wrapper.find('input[type="text"]')
    expect(input.exists()).toBe(true)
    expect(input.attributes('placeholder')).toBe('Search graph...')
  })

  it('shows no results panel when query is empty', () => {
    const wrapper = mountSearch()
    expect(wrapper.text()).not.toContain('results found')
    expect(wrapper.text()).not.toContain('No results')
  })

  it('searches nodes by name (local search)', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'VP Sales')
    expect(wrapper.text()).toContain('VP Sales')
    expect(wrapper.text()).toContain('Nodes')
  })

  it('searches nodes by summary', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'ML platform')
    expect(wrapper.text()).toContain('AI Platform')
  })

  it('searches edges by fact', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'evaluates')
    expect(wrapper.text()).toContain('VP Sales evaluates AI Platform for team use')
  })

  it('shows "No results" for non-matching query', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'xyznonexistent')
    expect(wrapper.text()).toContain('No results for "xyznonexistent"')
  })

  it('shows result count', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'VP Sales')
    expect(wrapper.text()).toMatch(/\d+ results? found/)
  })

  it('shows "Nodes (N)" header', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'VP Sales')
    expect(wrapper.text()).toMatch(/Nodes \(\d+\)/)
  })

  it('shows "Facts (N)" header', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'evaluates')
    expect(wrapper.text()).toMatch(/Facts \(\d+\)/)
  })

  it('clear button clears search', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'VP Sales')
    expect(wrapper.text()).toContain('Nodes')
    const clearBtn = wrapper.findAll('button').find(b => b.text().includes('\u00d7'))
    await clearBtn.trigger('click')
    await nextTick()
    expect(wrapper.find('input[type="text"]').element.value).toBe('')
    expect(wrapper.text()).not.toContain('results found')
  })

  it('escape key clears search', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'VP Sales')
    expect(wrapper.text()).toContain('Nodes')
    const input = wrapper.find('input[type="text"]')
    await input.trigger('keydown', { key: 'Escape' })
    await nextTick()
    expect(input.element.value).toBe('')
  })

  it('emits select-node with uuid on node click', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'VP Sales')
    const nodeBtn = wrapper.findAll('button').find(b => b.text().includes('VP Sales'))
    await nodeBtn.trigger('click')
    expect(wrapper.emitted('select-node')).toHaveLength(1)
    expect(wrapper.emitted('select-node')[0][0]).toBe('n1')
  })

  it('shows entity type label (Persona for persona nodes)', async () => {
    const wrapper = mountSearch()
    await typeAndSearch(wrapper, 'VP Sales')
    expect(wrapper.text()).toContain('Persona')
  })

  it('filters out generic labels (Entity, Node) from display', async () => {
    const wrapper = mountSearch({
      graphData: {
        nodes: [{ uuid: 'n1', name: 'TestNode', labels: ['Entity', 'Node', 'Persona'], summary: 'test' }],
        edges: [],
      },
    })
    await typeAndSearch(wrapper, 'TestNode')
    const typeLabels = wrapper.findAll('span').filter(s => s.text() === 'Entity')
    expect(typeLabels.length).toBe(0)
  })
})
