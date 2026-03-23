<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTask, createSimulation, prepareSimulation, poll } from '../api.js'

const props = defineProps({ taskId: String })
const route = useRoute()
const router = useRouter()

const status = ref('building')
const progress = ref(0)
const message = ref('Starting graph build...')
const nodeCount = ref(0)
const edgeCount = ref(0)
const error = ref(null)
const advancing = ref(false)

let poller = null

onMounted(() => {
  poller = poll(() => getTask(props.taskId))
  poller.start((result, err) => {
    if (err) {
      error.value = err.message
      status.value = 'failed'
      poller.stop()
      return
    }
    const task = result.data
    progress.value = task.progress || 0
    message.value = task.message || ''

    if (task.status === 'completed') {
      status.value = 'complete'
      const r = task.result || {}
      nodeCount.value = r.node_count || 0
      edgeCount.value = r.edge_count || 0
      poller.stop()
    } else if (task.status === 'failed') {
      status.value = 'failed'
      error.value = task.error || task.message || 'Graph build failed'
      poller.stop()
    }
  })
})

onUnmounted(() => {
  if (poller) poller.stop()
})

async function continueToSimulation() {
  if (advancing.value) return
  advancing.value = true
  error.value = null

  try {
    const projectId = route.query.projectId
    const platform = route.query.platform || 'parallel'

    // Get the task result to find graphId and projectId
    const taskResult = await getTask(props.taskId)
    const graphId = taskResult.data.result?.graph_id
    const resolvedProjectId = projectId || taskResult.data.result?.project_id

    if (!resolvedProjectId) throw new Error('Missing project ID')

    // Create simulation
    const enableTwitter = platform === 'twitter' || platform === 'parallel'
    const enableReddit = platform === 'reddit' || platform === 'parallel'
    const simResult = await createSimulation(resolvedProjectId, graphId, {
      enable_twitter: enableTwitter,
      enable_reddit: enableReddit,
    })
    const simulationId = simResult.data.simulation_id

    // Start preparing simulation (async, SimulationView will track)
    await prepareSimulation(simulationId)

    router.push({ name: 'simulation', params: { simulationId } })
  } catch (e) {
    error.value = e.message
    advancing.value = false
  }
}
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
      <div class="h-1 bg-white/10 rounded-full overflow-hidden">
        <div class="h-full bg-[#2068FF] rounded-full transition-all duration-500"
          :style="{ width: progress + '%' }"></div>
      </div>
      <p class="text-xs text-white/30 mt-2">{{ message }}</p>
    </div>

    <!-- Graph Canvas Placeholder -->
    <div class="flex items-center justify-center h-full">
      <div class="text-center text-white/30">
        <p class="text-6xl mb-4">🕸️</p>
        <p class="text-sm">D3.js Knowledge Graph</p>
        <p v-if="status === 'building'" class="text-xs mt-2 text-[#2068FF]">{{ progress }}% complete</p>
        <p v-if="status === 'complete'" class="text-xs mt-2 text-green-400">{{ nodeCount }} entities and {{ edgeCount }} relationships discovered</p>
        <p v-if="error" class="text-xs mt-2 text-red-400">{{ error }}</p>
      </div>
    </div>

    <!-- Continue Button -->
    <div v-if="status === 'complete'" class="absolute bottom-6 right-6">
      <button
        @click="continueToSimulation"
        :disabled="advancing"
        class="bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-60 text-white px-6 py-3 rounded-lg font-semibold text-sm transition-colors">
        <template v-if="advancing">Creating simulation...</template>
        <template v-else>Continue to Simulation →</template>
      </button>
    </div>
  </div>
</template>
