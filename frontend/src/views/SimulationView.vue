<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import { useToast } from '../composables/useToast'
import {
  createSimulation,
  prepareSimulation,
  getPrepareStatus,
  startSimulation,
  getRunStatus,
  getSimulationActions,
  pollTask,
} from '../services/api.js'

const props = defineProps({ taskId: String })
const route = useRoute()
const toast = useToast()

const projectId = ref(route.query.projectId || '')
const graphId = ref(route.query.graphId || '')
const simulationId = ref('')
const status = ref('initializing')
const phase = ref('')
const progress = ref(0)
const message = ref('Initializing simulation...')
const loading = ref(true)
const error = ref('')
const metrics = ref({ actions: 0, replies: 0, likes: 0, round: '0/0' })
const activities = ref([])

let cancelled = false
let pollInterval = null

async function initialize() {
  try {
    // Step 1: Create simulation
    phase.value = 'creating'
    message.value = 'Creating simulation...'
    const createRes = await createSimulation({
      projectId: projectId.value,
      graphId: graphId.value,
    })
    simulationId.value = createRes.data.simulation_id
    loading.value = false

    // Step 2: Prepare simulation (async — generates agent profiles)
    phase.value = 'preparing'
    status.value = 'preparing'
    message.value = 'Preparing agent profiles...'
    const prepRes = await prepareSimulation({
      simulationId: simulationId.value,
    })

    // If already prepared, skip polling
    if (!prepRes.data.already_prepared) {
      const taskId = prepRes.data.task_id
      await pollTask(
        () => getPrepareStatus({ taskId, simulationId: simulationId.value }),
        {
          interval: 3000,
          onProgress(data) {
            if (cancelled) return
            progress.value = data.progress || 0
            message.value = data.message || 'Generating agent profiles...'
          },
        },
      )
    }

    // Step 3: Start simulation
    phase.value = 'starting'
    status.value = 'running'
    message.value = 'Starting simulation run...'
    await startSimulation({
      simulationId: simulationId.value,
      platform: 'parallel',
    })

    // Step 4: Poll run status
    phase.value = 'running'
    pollRunStatus()
  } catch (e) {
    if (!cancelled) {
      status.value = 'failed'
      error.value = e.message
      loading.value = false
      toast.error(`Simulation error: ${e.message}`)
    }
  }
}

function pollRunStatus() {
  pollInterval = setInterval(async () => {
    if (cancelled) return
    try {
      const res = await getRunStatus(simulationId.value)
      const data = res.data
      const currentRound = data.current_round || 0
      const totalRounds = data.total_rounds || 0
      metrics.value = {
        actions: data.total_actions_count || 0,
        replies: data.reddit_actions_count || 0,
        likes: data.twitter_actions_count || 0,
        round: `${currentRound}/${totalRounds}`,
      }
      progress.value = data.progress_percent || 0

      if (data.runner_status === 'completed' || data.runner_status === 'stopped') {
        status.value = 'complete'
        clearInterval(pollInterval)
        pollInterval = null
        fetchActivities()
      }
    } catch (e) {
      console.warn('Run status poll error:', e)
    }
  }, 3000)
}

async function fetchActivities() {
  if (!simulationId.value) return
  try {
    const res = await getSimulationActions(simulationId.value, { limit: 20 })
    activities.value = (res.data?.actions || []).map((a) => ({
      agent: a.agent_name || `Agent ${a.agent_id}`,
      platform: a.platform,
      type: a.action_type,
      content: a.action_args?.content?.slice(0, 120) || a.action_type,
      round: a.round_num,
    }))
  } catch (e) {
    console.warn('Failed to fetch activities:', e)
  }
}

function retry() {
  loading.value = true
  error.value = ''
  initialize()
}

onMounted(() => {
  initialize()
})

onUnmounted(() => {
  cancelled = true
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-8">
    <!-- Loading State -->
    <LoadingSpinner v-if="loading" label="Connecting to simulation..." />

    <!-- Error State -->
    <ErrorState
      v-else-if="error"
      title="Simulation unavailable"
      :message="error"
      @retry="retry"
    />

    <!-- Simulation Content -->
    <template v-else>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 md:mb-8">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[#050505]">Live Simulation</h1>
        <p class="text-xs md:text-sm text-[#888]">{{ simulationId || 'Initializing...' }}</p>
      </div>
      <span class="self-start sm:self-auto px-4 py-1.5 rounded-full text-xs font-semibold"
        :class="{
          'bg-yellow-100 text-yellow-700': status === 'preparing' || status === 'initializing',
          'bg-green-100 text-green-700': status === 'running',
          'bg-blue-100 text-blue-700': status === 'complete',
          'bg-red-100 text-red-700': status === 'failed',
        }">
        {{ status === 'running' ? '● Running' : status === 'complete' ? '✓ Complete' : status === 'failed' ? '✗ Failed' : '◌ ' + (phase || 'Starting') }}
      </span>
    </div>

    <!-- Progress Bar (during prep/run) -->
    <div v-if="status !== 'complete' && status !== 'failed'" class="mb-6">
      <div class="bg-black/5 rounded-full h-2 overflow-hidden">
        <div class="bg-[#2068FF] h-full rounded-full transition-all duration-500" :style="{ width: progress + '%' }"></div>
      </div>
      <p class="text-xs text-[#888] mt-1">{{ message }}</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-6 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-4">
      {{ error }}
    </div>

    <!-- Metrics -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#2068FF]">{{ metrics.actions }}</div>
        <div class="text-xs text-[#888] mt-1">Total Actions</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#ff5600]">{{ metrics.replies }}</div>
        <div class="text-xs text-[#888] mt-1">Reddit Actions</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#A0F]">{{ metrics.likes }}</div>
        <div class="text-xs text-[#888] mt-1">Twitter Actions</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#090]">{{ metrics.round }}</div>
        <div class="text-xs text-[#888] mt-1">Round</div>
      </div>
    </div>

    <!-- Activity Feed -->
    <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
      <h3 class="text-sm font-semibold text-[#050505] mb-4">Agent Activity Feed</h3>
      <div v-if="activities.length === 0" class="text-center text-[#888] py-8">
        <p class="text-4xl mb-2">🐦</p>
        <p class="text-sm">{{ status === 'running' ? 'Waiting for agent actions...' : status === 'complete' ? 'Simulation completed' : 'Real-time agent actions will appear here' }}</p>
      </div>
      <div v-else class="space-y-3 max-h-80 overflow-y-auto">
        <div v-for="(act, i) in activities" :key="i"
          class="flex items-start gap-3 p-3 bg-[#fafafa] rounded-lg">
          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
            :class="act.platform === 'twitter' ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'">
            {{ act.platform }}
          </span>
          <div class="flex-1 min-w-0">
            <div class="text-xs font-medium text-[#050505]">{{ act.agent }} · Round {{ act.round }}</div>
            <div class="text-xs text-[#555] mt-0.5 truncate">{{ act.content }}</div>
          </div>
          <span class="text-[10px] text-[#aaa] uppercase shrink-0">{{ act.type }}</span>
        </div>
      </div>
    </div>

    <!-- Generate Report Button -->
    <div v-if="status === 'complete'" class="text-center mt-8">
      <router-link
        :to="{ path: `/report/${simulationId}`, query: { simulationId } }"
        class="inline-block bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-8 py-3 rounded-lg font-semibold transition-colors no-underline">
        Generate Report →
      </router-link>
    </div>
    </template>
  </div>
</template>
