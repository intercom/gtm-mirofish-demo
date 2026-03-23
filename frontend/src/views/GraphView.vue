<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { getGraphTask, getGraphData, pollTask } from '../services/api.js'

const props = defineProps({ taskId: String })
const route = useRoute()

const status = ref('building')
const progress = ref(0)
const message = ref('Starting graph build...')
const nodeCount = ref(0)
const edgeCount = ref(0)
const graphId = ref(null)
const projectId = ref(route.query.projectId || '')
const error = ref('')
const graphNodes = ref([])
const graphEdges = ref([])

let cancelled = false

onMounted(async () => {
  try {
    await pollTask(
      () => getGraphTask(props.taskId),
      {
        interval: 2000,
        onProgress(data) {
          if (cancelled) return
          progress.value = data.progress || 0
          message.value = data.message || ''
          if (data.result) {
            nodeCount.value = data.result.node_count || 0
            edgeCount.value = data.result.edge_count || 0
            graphId.value = data.result.graph_id
          }
        },
      },
    )

    status.value = 'complete'

    // Fetch actual graph data for visualization
    if (graphId.value) {
      try {
        const gdata = await getGraphData(graphId.value)
        graphNodes.value = gdata.data?.nodes || []
        graphEdges.value = gdata.data?.edges || []
        nodeCount.value = graphNodes.value.length || nodeCount.value
        edgeCount.value = graphEdges.value.length || edgeCount.value
      } catch (e) {
        console.warn('Could not fetch graph data for visualization:', e)
      }
    }
  } catch (e) {
    if (!cancelled) {
      status.value = 'failed'
      error.value = e.message
    }
  }
})

onUnmounted(() => {
  cancelled = true
})
</script>

<template>
  <div class="h-[calc(100vh-120px)] bg-[#0a0a1a] relative">
    <!-- Status Bar -->
    <div class="absolute top-4 left-4 z-10 flex items-center gap-3">
      <span class="px-3 py-1 rounded-full text-xs font-medium"
        :class="{
          'bg-yellow-500/20 text-yellow-400': status === 'building',
          'bg-green-500/20 text-green-400': status === 'complete',
          'bg-red-500/20 text-red-400': status === 'failed',
        }">
        {{ status === 'building' ? 'Building Graph...' : status === 'complete' ? 'Complete' : 'Failed' }}
      </span>
      <span class="text-xs text-white/40">{{ nodeCount }} nodes · {{ edgeCount }} edges</span>
    </div>

    <!-- Progress Bar -->
    <div v-if="status === 'building'" class="absolute top-14 left-4 right-4 z-10">
      <div class="bg-white/10 rounded-full h-1.5 overflow-hidden">
        <div class="bg-[#2068FF] h-full rounded-full transition-all duration-500" :style="{ width: progress + '%' }"></div>
      </div>
      <p class="text-xs text-white/30 mt-1">{{ message }}</p>
    </div>

    <!-- Graph Canvas -->
    <div class="flex items-center justify-center h-full">
      <div v-if="status === 'failed'" class="text-center">
        <p class="text-4xl mb-4">❌</p>
        <p class="text-sm text-red-400">Graph build failed</p>
        <p class="text-xs text-red-400/60 mt-2 max-w-md">{{ error }}</p>
      </div>
      <div v-else-if="graphNodes.length" class="text-center text-white/30">
        <p class="text-6xl mb-4">🕸️</p>
        <p class="text-sm">Knowledge Graph Ready</p>
        <p class="text-xs mt-2 text-white/40">{{ nodeCount }} entities and {{ edgeCount }} relationships extracted</p>
        <div class="mt-6 grid grid-cols-2 sm:grid-cols-3 gap-2 max-w-lg mx-auto">
          <div v-for="node in graphNodes.slice(0, 9)" :key="node.uuid || node.name"
            class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/50 truncate">
            {{ node.name || node.label || 'Entity' }}
          </div>
        </div>
      </div>
      <div v-else class="text-center text-white/30">
        <p class="text-6xl mb-4">🕸️</p>
        <p class="text-sm">{{ status === 'building' ? 'Building Knowledge Graph...' : 'Knowledge Graph' }}</p>
        <p class="text-xs mt-2">Task: {{ taskId }}</p>
      </div>
    </div>

    <!-- Error or Continue -->
    <div v-if="status === 'complete'" class="absolute bottom-6 right-6">
      <router-link
        :to="{ path: `/simulation/${graphId || taskId}`, query: { projectId, graphId } }"
        class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-6 py-3 rounded-lg font-semibold text-sm transition-colors no-underline">
        Continue to Simulation →
      </router-link>
    </div>
  </div>
</template>
