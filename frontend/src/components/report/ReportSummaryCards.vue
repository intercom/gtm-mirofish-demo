<script setup>
import { ref, onMounted } from 'vue'
import { API_BASE } from '../../api/client'
import { useCountUp } from '../../composables/useCountUp'

const props = defineProps({
  taskId: { type: String, required: true },
  sectionsCount: { type: Number, default: 0 },
})

const loading = ref(true)
const totalActions = ref(0)
const agentsCount = ref(0)
const totalRounds = ref(0)
const progressPercent = ref(0)

const displayActions = useCountUp(totalActions)
const displayAgents = useCountUp(agentsCount)
const displayRounds = useCountUp(totalRounds)

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/simulation/${props.taskId}/run-status`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success && json.data) {
      totalActions.value = json.data.total_actions_count || 0
      totalRounds.value = json.data.current_round || json.data.total_rounds || 0
      progressPercent.value = json.data.progress_percent || 0
    }
  } catch {
    // Stats are supplementary — silently degrade
  }

  try {
    const res = await fetch(`${API_BASE}/simulation/${props.taskId}/agent-stats`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success && json.data) {
      agentsCount.value = json.data.agents_count || 0
    }
  } catch {
    // Silently degrade
  }

  loading.value = false
}

onMounted(fetchStats)

const cards = [
  { key: 'agents', label: 'Agents Simulated', icon: 'users', color: '#2068FF' },
  { key: 'actions', label: 'Total Actions', icon: 'activity', color: '#ff5600' },
  { key: 'rounds', label: 'Rounds Complete', icon: 'rounds', color: '#009900' },
  { key: 'sections', label: 'Report Sections', icon: 'doc', color: '#AA00FF' },
]

function getValue(key) {
  switch (key) {
    case 'agents': return displayAgents.value
    case 'actions': return displayActions.value
    case 'rounds': return displayRounds.value
    case 'sections': return props.sectionsCount
    default: return 0
  }
}
</script>

<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
    <div
      v-for="card in cards"
      :key="card.key"
      class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 transition-shadow hover:shadow-sm"
    >
      <div class="flex items-center gap-2 mb-2">
        <!-- Users icon -->
        <svg v-if="card.icon === 'users'" class="w-4 h-4" :style="{ color: card.color }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <!-- Activity icon -->
        <svg v-else-if="card.icon === 'activity'" class="w-4 h-4" :style="{ color: card.color }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <!-- Rounds icon -->
        <svg v-else-if="card.icon === 'rounds'" class="w-4 h-4" :style="{ color: card.color }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <!-- Doc icon -->
        <svg v-else-if="card.icon === 'doc'" class="w-4 h-4" :style="{ color: card.color }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span class="text-xs font-medium text-[var(--color-text-muted)]">{{ card.label }}</span>
      </div>
      <div v-if="loading && card.key !== 'sections'" class="h-8 w-16 rounded bg-[var(--color-tint)] animate-pulse" />
      <p v-else class="text-2xl font-semibold text-[var(--color-text)]" :style="{ color: card.color }">
        {{ getValue(card.key).toLocaleString() }}
      </p>
    </div>
  </div>
</template>
