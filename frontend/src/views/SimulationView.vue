<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useToastStore } from '../stores/toast.js'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const props = defineProps({ taskId: String })
const toast = useToastStore()

const status = ref('loading')
const error = ref(null)
const metrics = ref({ actions: 0, replies: 0, likes: 0, round: '0/24' })
const activities = ref([])
let pollTimer = null

async function loadSimulation() {
  status.value = 'loading'
  error.value = null
  try {
    // TODO: Poll /api/simulation/status every 3s
    // Parse JSONL activity logs
    status.value = 'running'
    toast.info('Simulation is running...')
  } catch (e) {
    status.value = 'error'
    error.value = 'Failed to load simulation: ' + e.message
    toast.error(error.value)
  }
}

onMounted(loadSimulation)
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <!-- Loading -->
    <LoadingSpinner v-if="status === 'loading'" label="Connecting to simulation..." />

    <!-- Error -->
    <ErrorState v-else-if="status === 'error'" :message="error" @retry="loadSimulation" />

    <!-- Running / Complete -->
    <template v-else>
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-semibold text-[#050505]">Live Simulation</h1>
          <p class="text-sm text-[#888]">Task: {{ taskId }}</p>
        </div>
        <span class="px-4 py-1.5 rounded-full text-xs font-semibold"
          :class="status === 'running' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'">
          {{ status === 'running' ? '● Running' : '✓ Complete' }}
        </span>
      </div>

      <!-- Metrics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
          <div class="text-3xl font-semibold text-[#2068FF]">{{ metrics.actions }}</div>
          <div class="text-xs text-[#888] mt-1">Total Actions</div>
        </div>
        <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
          <div class="text-3xl font-semibold text-[#ff5600]">{{ metrics.replies }}</div>
          <div class="text-xs text-[#888] mt-1">Replies</div>
        </div>
        <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
          <div class="text-3xl font-semibold text-[#A0F]">{{ metrics.likes }}</div>
          <div class="text-xs text-[#888] mt-1">Likes</div>
        </div>
        <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
          <div class="text-3xl font-semibold text-[#090]">{{ metrics.round }}</div>
          <div class="text-xs text-[#888] mt-1">Round</div>
        </div>
      </div>

      <!-- Activity Feed -->
      <div class="bg-white border border-black/10 rounded-lg p-6">
        <h3 class="text-sm font-semibold text-[#050505] mb-4">Agent Activity Feed</h3>
        <EmptyState
          v-if="activities.length === 0"
          icon="🐦"
          title="Waiting for agent activity"
          description="Real-time posts, replies, likes, and reposts from simulated agents will appear here as the simulation runs."
        />
        <div v-else class="space-y-3">
          <div v-for="(activity, i) in activities" :key="i"
            class="flex items-start gap-3 p-3 rounded-lg bg-[#fafafa] text-sm">
            <span class="text-lg">{{ activity.icon || '🐟' }}</span>
            <div>
              <span class="font-medium text-[#050505]">{{ activity.agent }}</span>
              <span class="text-[#888] ml-1">{{ activity.action }}</span>
              <p v-if="activity.content" class="text-[#555] mt-1">{{ activity.content }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Generate Report Button -->
      <div v-if="status === 'complete'" class="text-center mt-8">
        <router-link :to="`/report/${taskId}`"
          class="inline-block bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-8 py-3 rounded-lg font-semibold transition-colors no-underline">
          Generate Report →
        </router-link>
      </div>
    </template>
  </div>
</template>
