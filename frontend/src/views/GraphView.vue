<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useToastStore } from '../stores/toast.js'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'

const props = defineProps({ taskId: String })
const toast = useToastStore()

const graphData = ref({ nodes: [], edges: [] })
const status = ref('loading')
const error = ref(null)
const nodeCount = ref(0)
const edgeCount = ref(0)
let pollTimer = null

async function loadGraph() {
  status.value = 'loading'
  error.value = null
  try {
    // TODO: Poll /api/graph/status until complete, then render
    // Simulating initial load for now
    status.value = 'building'
    toast.info('Building knowledge graph...')
  } catch (e) {
    status.value = 'error'
    error.value = 'Failed to build knowledge graph: ' + e.message
    toast.error(error.value)
  }
}

onMounted(loadGraph)
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<template>
  <div class="h-[calc(100vh-120px)] bg-[#0a0a1a] relative">
    <!-- Loading State -->
    <div v-if="status === 'loading'" class="flex items-center justify-center h-full">
      <LoadingSpinner label="Initializing graph engine..." size="lg" />
    </div>

    <!-- Error State -->
    <div v-else-if="status === 'error'" class="flex items-center justify-center h-full">
      <ErrorState :message="error" @retry="loadGraph" />
    </div>

    <!-- Building / Complete -->
    <template v-else>
      <!-- Status Bar -->
      <div class="absolute top-4 left-4 z-10 flex items-center gap-3">
        <span class="px-3 py-1 rounded-full text-xs font-medium"
          :class="status === 'building' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'">
          {{ status === 'building' ? 'Building Graph...' : 'Complete' }}
        </span>
        <span class="text-xs text-white/40">{{ nodeCount }} nodes · {{ edgeCount }} edges</span>
      </div>

      <!-- Graph Canvas Placeholder -->
      <div class="flex items-center justify-center h-full">
        <div class="text-center text-white/30">
          <p class="text-6xl mb-4">🕸️</p>
          <p class="text-sm">D3.js Knowledge Graph</p>
          <p class="text-xs mt-2">Task: {{ taskId }}</p>
          <p class="text-xs text-white/20 mt-4">This view will render an interactive force-directed graph<br/>with entity nodes, relationship edges, and click-to-inspect details.</p>
        </div>
      </div>

      <!-- Continue Button -->
      <div v-if="status === 'complete'" class="absolute bottom-6 right-6">
        <router-link :to="`/simulation/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-6 py-3 rounded-lg font-semibold text-sm transition-colors no-underline">
          Continue to Simulation →
        </router-link>
      </div>
    </template>
  </div>
</template>
