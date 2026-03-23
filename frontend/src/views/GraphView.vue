<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({ taskId: String })
const graphData = ref({ nodes: [], edges: [] })
const status = ref('building')
const nodeCount = ref(0)
const edgeCount = ref(0)

// TODO: Implement D3.js force-directed graph visualization
// Poll /api/graph/status until complete, then render
</script>

<template>
  <div class="h-[calc(100vh-120px)] bg-[#0a0a1a] relative">
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
  </div>
</template>
