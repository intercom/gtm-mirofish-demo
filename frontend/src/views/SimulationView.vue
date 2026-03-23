<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getPrepareStatus,
  startSimulation,
  getRunStatus,
  getSimulationActions,
  poll,
} from '../api.js'

const props = defineProps({ simulationId: String })
const router = useRouter()

const phase = ref('preparing') // preparing | starting | running | complete | failed
const status = ref('preparing')
const prepareProgress = ref(0)
const prepareMessage = ref('Preparing simulation environment...')
const metrics = ref({ actions: 0, replies: 0, likes: 0, round: '0/0' })
const activities = ref([])
const error = ref(null)

let preparePoller = null
let runPoller = null
let actionsPoller = null

onMounted(() => {
  pollPrepareStatus()
})

onUnmounted(() => {
  if (preparePoller) preparePoller.stop()
  if (runPoller) runPoller.stop()
  if (actionsPoller) actionsPoller.stop()
})

function pollPrepareStatus() {
  phase.value = 'preparing'
  preparePoller = poll(
    () => getPrepareStatus(null, props.simulationId),
    3000,
  )
  preparePoller.start(async (result, err) => {
    if (err) {
      // Prepare status may 400 if no task — check with simulation_id
      error.value = err.message
      return
    }
    const d = result.data
    prepareProgress.value = d.progress || 0
    prepareMessage.value = d.message || ''

    if (d.status === 'ready' || d.already_prepared) {
      preparePoller.stop()
      await launchSimulation()
    } else if (d.status === 'completed') {
      preparePoller.stop()
      await launchSimulation()
    } else if (d.status === 'failed') {
      preparePoller.stop()
      phase.value = 'failed'
      error.value = d.message || 'Preparation failed'
    }
  })
}

async function launchSimulation() {
  phase.value = 'starting'
  try {
    await startSimulation(props.simulationId, 'parallel')
    phase.value = 'running'
    status.value = 'running'
    startRunPolling()
  } catch (e) {
    // If it's already running, just start polling
    if (e.message && e.message.includes('正在运行')) {
      phase.value = 'running'
      status.value = 'running'
      startRunPolling()
    } else {
      phase.value = 'failed'
      error.value = e.message
    }
  }
}

function startRunPolling() {
  runPoller = poll(() => getRunStatus(props.simulationId), 3000)
  runPoller.start((result, err) => {
    if (err) return
    const d = result.data
    const totalActions = d.total_actions_count || 0
    const twitterActions = d.twitter_actions_count || 0
    const redditActions = d.reddit_actions_count || 0
    const currentRound = d.current_round || 0
    const totalRounds = d.total_rounds || 0

    metrics.value = {
      actions: totalActions,
      replies: redditActions,
      likes: twitterActions,
      round: `${currentRound}/${totalRounds}`,
    }

    if (d.runner_status === 'completed' || d.runner_status === 'stopped') {
      status.value = 'complete'
      phase.value = 'complete'
      runPoller.stop()
      if (actionsPoller) actionsPoller.stop()
    }
  })

  // Also poll for activity feed
  actionsPoller = poll(() => getSimulationActions(props.simulationId, 20), 5000)
  actionsPoller.start((result, err) => {
    if (err) return
    activities.value = (result.data?.actions || []).reverse()
  })
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-[#050505]">Live Simulation</h1>
        <p class="text-sm text-[#888]">ID: {{ simulationId }}</p>
      </div>
      <span class="px-4 py-1.5 rounded-full text-xs font-semibold"
        :class="{
          'bg-yellow-100 text-yellow-700': phase === 'preparing' || phase === 'starting',
          'bg-green-100 text-green-700': phase === 'running',
          'bg-blue-100 text-blue-700': phase === 'complete',
          'bg-red-100 text-red-700': phase === 'failed',
        }">
        {{ phase === 'preparing' ? '⏳ Preparing...' :
           phase === 'starting' ? '🚀 Starting...' :
           phase === 'running' ? '● Running' :
           phase === 'complete' ? '✓ Complete' : '✗ Failed' }}
      </span>
    </div>

    <!-- Prepare Progress -->
    <div v-if="phase === 'preparing' || phase === 'starting'" class="mb-8">
      <div class="bg-white border border-black/10 rounded-lg p-6">
        <h3 class="text-sm font-semibold text-[#050505] mb-3">
          {{ phase === 'preparing' ? 'Preparing Environment' : 'Starting Simulation' }}
        </h3>
        <div class="h-2 bg-black/5 rounded-full overflow-hidden mb-2">
          <div class="h-full bg-[#2068FF] rounded-full transition-all duration-500"
            :style="{ width: (phase === 'starting' ? 100 : prepareProgress) + '%' }"></div>
        </div>
        <p class="text-xs text-[#888]">{{ phase === 'starting' ? 'Launching agents...' : prepareMessage }}</p>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-8 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Metrics -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
        <div class="text-3xl font-semibold text-[#2068FF]">{{ metrics.actions }}</div>
        <div class="text-xs text-[#888] mt-1">Total Actions</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
        <div class="text-3xl font-semibold text-[#ff5600]">{{ metrics.replies }}</div>
        <div class="text-xs text-[#888] mt-1">Reddit Actions</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
        <div class="text-3xl font-semibold text-[#A0F]">{{ metrics.likes }}</div>
        <div class="text-xs text-[#888] mt-1">Twitter Actions</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
        <div class="text-3xl font-semibold text-[#090]">{{ metrics.round }}</div>
        <div class="text-xs text-[#888] mt-1">Round</div>
      </div>
    </div>

    <!-- Activity Feed -->
    <div class="bg-white border border-black/10 rounded-lg p-6">
      <h3 class="text-sm font-semibold text-[#050505] mb-4">Agent Activity Feed</h3>
      <div v-if="activities.length === 0" class="text-center text-[#888] py-8">
        <p class="text-4xl mb-2">🐦</p>
        <p class="text-sm">{{ phase === 'running' ? 'Waiting for agent actions...' : 'Real-time agent actions will appear here' }}</p>
      </div>
      <div v-else class="space-y-3 max-h-80 overflow-y-auto">
        <div v-for="(action, i) in activities" :key="i"
          class="flex items-start gap-3 p-3 rounded-lg bg-[#fafafa]">
          <span class="text-lg">{{ action.platform === 'twitter' ? '🐦' : '💬' }}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold text-[#050505]">{{ action.agent_name || `Agent ${action.agent_id}` }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-black/5 text-[#888]">{{ action.action_type }}</span>
              <span class="text-[10px] text-[#aaa]">R{{ action.round_num }}</span>
            </div>
            <p class="text-xs text-[#555] truncate">{{ action.action_args?.content || action.action_args?.text || '' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Generate Report Button -->
    <div v-if="phase === 'complete'" class="text-center mt-8">
      <router-link :to="{ name: 'report', params: { simulationId } }"
        class="inline-block bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-8 py-3 rounded-lg font-semibold transition-colors no-underline">
        Generate Report →
      </router-link>
    </div>
  </div>
</template>
