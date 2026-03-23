<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({ taskId: String })
const graphData = ref({ nodes: [], edges: [] })
const status = ref('building')
const nodeCount = ref(0)
const edgeCount = ref(0)
const visibleNodes = ref([])

const placeholderNodes = [
  { id: 1, label: 'Campaign', color: '#2068FF', x: 50, y: 40, size: 48 },
  { id: 2, label: 'Audience', color: '#ff5600', x: 30, y: 60, size: 40 },
  { id: 3, label: 'Channel', color: '#A0F', x: 70, y: 55, size: 36 },
  { id: 4, label: 'Signal', color: '#090', x: 45, y: 25, size: 32 },
  { id: 5, label: 'Outcome', color: '#2068FF', x: 65, y: 75, size: 44 },
  { id: 6, label: 'Persona', color: '#ff5600', x: 25, y: 35, size: 34 },
  { id: 7, label: 'Objection', color: '#A0F', x: 75, y: 30, size: 30 },
]

function onNodeBeforeEnter(el) {
  el.style.opacity = 0
  el.style.transform = 'scale(0.6)'
}

function onNodeEnter(el, done) {
  const delay = el.dataset.index * 120
  setTimeout(() => {
    el.style.transition = 'opacity var(--transition-slow), transform var(--transition-slow)'
    el.style.opacity = 1
    el.style.transform = 'scale(1)'
    el.addEventListener('transitionend', done, { once: true })
  }, delay)
}

onMounted(() => {
  // Simulate nodes appearing as graph builds
  visibleNodes.value = placeholderNodes
  nodeCount.value = placeholderNodes.length
  edgeCount.value = 9
  setTimeout(() => { status.value = 'complete' }, 1500)
})

// TODO: Implement D3.js force-directed graph visualization
// Poll /api/graph/status until complete, then render
</script>

<template>
  <div class="h-[calc(100vh-120px)] bg-[#0a0a1a] relative overflow-hidden">
    <!-- Status Bar -->
    <div class="absolute top-4 left-4 z-10 flex items-center gap-3">
      <span class="px-3 py-1 rounded-full text-xs font-medium"
        :class="status === 'building' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'">
        {{ status === 'building' ? 'Building Graph...' : 'Complete' }}
      </span>
      <span class="text-xs text-white/40">{{ nodeCount }} nodes · {{ edgeCount }} edges</span>
    </div>

    <!-- Animated Graph Nodes -->
    <TransitionGroup
      :css="false"
      @before-enter="onNodeBeforeEnter"
      @enter="onNodeEnter"
    >
      <div
        v-for="(node, i) in visibleNodes"
        :key="node.id"
        :data-index="i"
        class="absolute rounded-full flex items-center justify-center text-white text-[10px] font-medium shadow-lg"
        :style="{
          left: node.x + '%',
          top: node.y + '%',
          width: node.size + 'px',
          height: node.size + 'px',
          backgroundColor: node.color + '33',
          border: '2px solid ' + node.color,
          transform: 'translate(-50%, -50%)',
        }"
      >
        {{ node.label }}
      </div>
    </TransitionGroup>

    <!-- Edge lines (decorative SVG) -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none" style="z-index: 0;">
      <line v-for="(edge, i) in [
        [50, 40, 30, 60], [50, 40, 70, 55], [50, 40, 45, 25],
        [30, 60, 65, 75], [70, 55, 65, 75], [45, 25, 75, 30],
        [25, 35, 50, 40], [25, 35, 30, 60], [70, 55, 75, 30],
      ]" :key="i"
        :x1="edge[0] + '%'" :y1="edge[1] + '%'"
        :x2="edge[2] + '%'" :y2="edge[3] + '%'"
        stroke="rgba(255,255,255,0.08)" stroke-width="1"
      />
    </svg>

    <!-- Center Label -->
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div class="text-center text-white/20">
        <p class="text-xs">Task: {{ taskId }}</p>
        <p class="text-[10px] mt-1">D3.js force-directed graph will replace this preview</p>
      </div>
    </div>

    <!-- Continue Button -->
    <Transition name="page">
      <div v-if="status === 'complete'" class="absolute bottom-6 right-6">
        <router-link :to="`/simulation/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-6 py-3 rounded-lg font-semibold text-sm transition-colors no-underline">
          Continue to Simulation →
        </router-link>
      </div>
    </Transition>
  </div>
</template>
