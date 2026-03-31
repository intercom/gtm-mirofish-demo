import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/graph', () => ({
  graphApi: {
    getData: vi.fn(),
    searchGraph: vi.fn(),
  },
}))

import { useGraphStore } from '../graph'
import { graphApi } from '@/api/graph'

const makeNode = (uuid, labels = ['Entity'], name = '') => ({ uuid, labels, name })
const makeEdge = (source, target, extras = {}) => ({
  source_node_uuid: source,
  target_node_uuid: target,
  ...extras,
})

describe('useGraphStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('has correct initial state', () => {
    const store = useGraphStore()
    expect(store.nodes).toEqual([])
    expect(store.edges).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.graphId).toBeNull()
    expect(store.selectedNodeId).toBeNull()
    expect(store.searchQuery).toBe('')
    expect(store.activeTypeFilters).toEqual([])
    expect(store.highlightedNodeIds).toEqual(new Set())
    expect(store.chargeStrength).toBe(-300)
    expect(store.linkDistance).toBe(120)
  })

  // --- entityTypes computed ---

  it('entityTypes groups nodes by first meaningful label and sorts by count descending', () => {
    const store = useGraphStore()
    store.nodes = [
      makeNode('1', ['Entity', 'Person']),
      makeNode('2', ['Person', 'Entity']),
      makeNode('3', ['Company']),
      makeNode('4', ['Company']),
      makeNode('5', ['Company']),
      makeNode('6', ['Company']),
    ]
    expect(store.entityTypes).toEqual([
      { type: 'Company', count: 4 },
      { type: 'Person', count: 2 },
    ])
  })

  it('entityTypes falls back to Entity when all labels are generic', () => {
    const store = useGraphStore()
    store.nodes = [
      makeNode('1', ['Entity']),
      makeNode('2', ['Node']),
      makeNode('3', []),
    ]
    expect(store.entityTypes).toEqual([{ type: 'Entity', count: 3 }])
  })

  it('entityTypes filters out generic Entity and Node labels', () => {
    const store = useGraphStore()
    store.nodes = [
      makeNode('1', ['Node', 'Product']),
      makeNode('2', ['Entity', 'Product']),
    ]
    expect(store.entityTypes).toEqual([{ type: 'Product', count: 2 }])
  })

  // --- filteredNodes computed ---

  it('filteredNodes returns all nodes when no filters active', () => {
    const store = useGraphStore()
    store.nodes = [makeNode('1', ['Person']), makeNode('2', ['Company'])]
    expect(store.filteredNodes).toHaveLength(2)
  })

  it('filteredNodes filters by activeTypeFilters', () => {
    const store = useGraphStore()
    store.nodes = [
      makeNode('1', ['Person']),
      makeNode('2', ['Company']),
      makeNode('3', ['Person']),
    ]
    store.activeTypeFilters = ['Person']
    expect(store.filteredNodes).toHaveLength(2)
    expect(store.filteredNodes.every(n => n.labels.includes('Person'))).toBe(true)
  })

  // --- filteredEdges computed ---

  it('filteredEdges only includes edges between filtered nodes', () => {
    const store = useGraphStore()
    store.nodes = [
      makeNode('1', ['Person']),
      makeNode('2', ['Company']),
      makeNode('3', ['Person']),
    ]
    store.edges = [
      makeEdge('1', '2'),
      makeEdge('1', '3'),
      makeEdge('2', '3'),
    ]
    store.activeTypeFilters = ['Person']
    expect(store.filteredEdges).toHaveLength(1)
    expect(store.filteredEdges[0]).toEqual(makeEdge('1', '3'))
  })

  // --- selectedNode computed ---

  it('selectedNode returns null when no selection', () => {
    const store = useGraphStore()
    expect(store.selectedNode).toBeNull()
  })

  it('selectedNode returns the matching node', () => {
    const store = useGraphStore()
    store.nodes = [makeNode('1', ['Person'], 'Alice'), makeNode('2', ['Company'], 'Acme')]
    store.selectNode('2')
    expect(store.selectedNode).toEqual(makeNode('2', ['Company'], 'Acme'))
  })

  it('selectedNode returns null for non-existent nodeId', () => {
    const store = useGraphStore()
    store.nodes = [makeNode('1', ['Person'])]
    store.selectNode('missing')
    expect(store.selectedNode).toBeNull()
  })

  // --- selectedNodeConnections computed ---

  it('selectedNodeConnections returns empty when no selection', () => {
    const store = useGraphStore()
    expect(store.selectedNodeConnections).toEqual([])
  })

  it('selectedNodeConnections maps outgoing and incoming edges', () => {
    const store = useGraphStore()
    store.nodes = [
      makeNode('a', ['Person'], 'Alice'),
      makeNode('b', ['Company'], 'Acme'),
      makeNode('c', ['Person'], 'Bob'),
    ]
    store.edges = [
      makeEdge('a', 'b', { name: 'works_at', fact: 'Alice works at Acme' }),
      makeEdge('c', 'a', { name: 'knows', fact: 'Bob knows Alice' }),
    ]
    store.selectNode('a')
    const connections = store.selectedNodeConnections
    expect(connections).toHaveLength(2)

    const outgoing = connections.find(c => c.direction === 'outgoing')
    expect(outgoing.name).toBe('works_at')
    expect(outgoing.targetName).toBe('Acme')

    const incoming = connections.find(c => c.direction === 'incoming')
    expect(incoming.name).toBe('knows')
    expect(incoming.targetName).toBe('Bob')
  })

  it('selectedNodeConnections uses fact_type as fallback for name', () => {
    const store = useGraphStore()
    store.nodes = [makeNode('a', ['Person'], 'Alice'), makeNode('b', ['Person'], 'Bob')]
    store.edges = [makeEdge('a', 'b', { fact_type: 'friend_of', fact: 'friends' })]
    store.selectNode('a')
    expect(store.selectedNodeConnections[0].name).toBe('friend_of')
  })

  // --- selectNode / clearSelection ---

  it('selectNode sets selectedNodeId', () => {
    const store = useGraphStore()
    store.selectNode('node-1')
    expect(store.selectedNodeId).toBe('node-1')
  })

  it('clearSelection resets selectedNodeId', () => {
    const store = useGraphStore()
    store.selectNode('node-1')
    store.clearSelection()
    expect(store.selectedNodeId).toBeNull()
  })

  // --- toggleTypeFilter / clearFilters ---

  it('toggleTypeFilter adds a type', () => {
    const store = useGraphStore()
    store.toggleTypeFilter('Person')
    expect(store.activeTypeFilters).toEqual(['Person'])
  })

  it('toggleTypeFilter removes an existing type', () => {
    const store = useGraphStore()
    store.toggleTypeFilter('Person')
    store.toggleTypeFilter('Person')
    expect(store.activeTypeFilters).toEqual([])
  })

  it('clearFilters resets filters, search query, and highlighted nodes', () => {
    const store = useGraphStore()
    store.toggleTypeFilter('Person')
    store.searchQuery = 'test'
    store.highlightedNodeIds = new Set(['1', '2'])
    store.clearFilters()
    expect(store.activeTypeFilters).toEqual([])
    expect(store.searchQuery).toBe('')
    expect(store.highlightedNodeIds).toEqual(new Set())
  })

  // --- fetchGraphData ---

  it('fetchGraphData sets nodes and edges on success', async () => {
    graphApi.getData.mockResolvedValue({
      data: { data: { nodes: [makeNode('1', ['Person'])], edges: [makeEdge('1', '2')] } },
    })
    const store = useGraphStore()
    await store.fetchGraphData('graph-1')
    expect(store.nodes).toHaveLength(1)
    expect(store.edges).toHaveLength(1)
    expect(store.graphId).toBe('graph-1')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchGraphData handles flat data response', async () => {
    graphApi.getData.mockResolvedValue({
      data: { nodes: [makeNode('1', ['Person'])], edges: [] },
    })
    const store = useGraphStore()
    await store.fetchGraphData('graph-1')
    expect(store.nodes).toHaveLength(1)
    expect(store.edges).toEqual([])
  })

  it('fetchGraphData sets error on failure', async () => {
    graphApi.getData.mockRejectedValue(new Error('Network error'))
    const store = useGraphStore()
    await store.fetchGraphData('graph-1')
    expect(store.error).toBe('Network error')
    expect(store.nodes).toEqual([])
    expect(store.edges).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('fetchGraphData sets loading during request', async () => {
    let resolve
    graphApi.getData.mockReturnValue(new Promise(r => { resolve = r }))
    const store = useGraphStore()
    const promise = store.fetchGraphData('graph-1')
    expect(store.loading).toBe(true)
    resolve({ data: { data: { nodes: [], edges: [] } } })
    await promise
    expect(store.loading).toBe(false)
  })

  // --- searchGraph ---

  it('searchGraph sets highlighted node ids on success', async () => {
    graphApi.searchGraph.mockResolvedValue({
      data: { data: { matched_node_ids: ['1', '3'] } },
    })
    const store = useGraphStore()
    await store.searchGraph('graph-1', 'alice')
    expect(store.highlightedNodeIds).toEqual(new Set(['1', '3']))
  })

  it('searchGraph clears highlights when query is empty', async () => {
    const store = useGraphStore()
    store.highlightedNodeIds = new Set(['1'])
    await store.searchGraph('graph-1', '   ')
    expect(store.highlightedNodeIds).toEqual(new Set())
    expect(graphApi.searchGraph).not.toHaveBeenCalled()
  })

  it('searchGraph clears highlights on error', async () => {
    graphApi.searchGraph.mockRejectedValue(new Error('fail'))
    const store = useGraphStore()
    store.highlightedNodeIds = new Set(['1'])
    await store.searchGraph('graph-1', 'query')
    expect(store.highlightedNodeIds).toEqual(new Set())
  })

  // --- reset ---

  it('reset clears all state to initial values', () => {
    const store = useGraphStore()
    store.nodes = [makeNode('1', ['Person'])]
    store.edges = [makeEdge('1', '2')]
    store.loading = true
    store.error = 'some error'
    store.graphId = 'graph-1'
    store.selectedNodeId = 'node-1'
    store.searchQuery = 'test'
    store.activeTypeFilters = ['Person']
    store.highlightedNodeIds = new Set(['1'])
    store.chargeStrength = -500
    store.linkDistance = 200

    store.reset()

    expect(store.nodes).toEqual([])
    expect(store.edges).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.graphId).toBeNull()
    expect(store.selectedNodeId).toBeNull()
    expect(store.searchQuery).toBe('')
    expect(store.activeTypeFilters).toEqual([])
    expect(store.highlightedNodeIds).toEqual(new Set())
    expect(store.chargeStrength).toBe(-300)
    expect(store.linkDistance).toBe(120)
  })
})
