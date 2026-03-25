import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { graphApi } from '@/api/graph'

const GENERIC_LABELS = new Set(['Entity', 'Node'])

export const useGraphStore = defineStore('graph', () => {
  const nodes = ref([])
  const edges = ref([])
  const loading = ref(false)
  const error = ref(null)
  const graphId = ref(null)

  const selectedNodeId = ref(null)
  const searchQuery = ref('')
  const activeTypeFilters = ref([])
  const highlightedNodeIds = ref(new Set())

  const chargeStrength = ref(-300)
  const linkDistance = ref(120)

  const entityTypes = computed(() => {
    const counts = {}
    for (const n of nodes.value) {
      const meaningful = (n.labels || []).filter(l => !GENERIC_LABELS.has(l))
      const type = meaningful[0] || 'Entity'
      counts[type] = (counts[type] || 0) + 1
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => ({ type, count }))
  })

  const filteredNodes = computed(() => {
    if (!activeTypeFilters.value.length) return nodes.value
    return nodes.value.filter(n => {
      const meaningful = (n.labels || []).filter(l => !GENERIC_LABELS.has(l))
      const type = meaningful[0] || 'Entity'
      return activeTypeFilters.value.includes(type)
    })
  })

  const filteredEdges = computed(() => {
    const nodeIds = new Set(filteredNodes.value.map(n => n.uuid))
    return edges.value.filter(
      e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid),
    )
  })

  const selectedNode = computed(() => {
    if (!selectedNodeId.value) return null
    return nodes.value.find(n => n.uuid === selectedNodeId.value) || null
  })

  const selectedNodeConnections = computed(() => {
    if (!selectedNodeId.value) return []
    return edges.value
      .filter(e => e.source_node_uuid === selectedNodeId.value || e.target_node_uuid === selectedNodeId.value)
      .map(e => ({
        name: e.name || e.fact_type || '',
        fact: e.fact || '',
        direction: e.source_node_uuid === selectedNodeId.value ? 'outgoing' : 'incoming',
        targetName: e.source_node_uuid === selectedNodeId.value
          ? (nodes.value.find(n => n.uuid === e.target_node_uuid)?.name || '')
          : (nodes.value.find(n => n.uuid === e.source_node_uuid)?.name || ''),
      }))
  })

  async function fetchGraphData(id) {
    loading.value = true
    error.value = null
    graphId.value = id
    try {
      const res = await graphApi.getData(id)
      const data = res.data?.data || res.data
      nodes.value = data.nodes || []
      edges.value = data.edges || []
    } catch (err) {
      error.value = err.message || 'Failed to load graph data'
    } finally {
      loading.value = false
    }
  }

  async function searchGraph(id, query) {
    if (!query.trim()) {
      highlightedNodeIds.value = new Set()
      return
    }
    try {
      const res = await graphApi.search(id, query)
      const data = res.data?.data || res.data
      highlightedNodeIds.value = new Set(data.matched_node_ids || [])
    } catch {
      highlightedNodeIds.value = new Set()
    }
  }

  function selectNode(nodeId) {
    selectedNodeId.value = nodeId
  }

  function clearSelection() {
    selectedNodeId.value = null
  }

  function toggleTypeFilter(type) {
    const idx = activeTypeFilters.value.indexOf(type)
    if (idx === -1) {
      activeTypeFilters.value.push(type)
    } else {
      activeTypeFilters.value.splice(idx, 1)
    }
  }

  function clearFilters() {
    activeTypeFilters.value = []
    searchQuery.value = ''
    highlightedNodeIds.value = new Set()
  }

  function reset() {
    nodes.value = []
    edges.value = []
    loading.value = false
    error.value = null
    graphId.value = null
    selectedNodeId.value = null
    searchQuery.value = ''
    activeTypeFilters.value = []
    highlightedNodeIds.value = new Set()
    chargeStrength.value = -300
    linkDistance.value = 120
  }

  return {
    nodes,
    edges,
    loading,
    error,
    graphId,
    selectedNodeId,
    searchQuery,
    activeTypeFilters,
    highlightedNodeIds,
    chargeStrength,
    linkDistance,
    entityTypes,
    filteredNodes,
    filteredEdges,
    selectedNode,
    selectedNodeConnections,
    fetchGraphData,
    searchGraph,
    selectNode,
    clearSelection,
    toggleTypeFilter,
    clearFilters,
    reset,
  }
})
